from collections.abc import Iterator
from datetime import timedelta

import pandas as pd
from bs4 import BeautifulSoup
from dagster import (
    AssetExecutionContext,
    Output,
    RetryPolicy,
    TimeWindow,
    asset,
)

from betsim.pipeline.io import write_artefact, write_cache, load_cache
from betsim.pipeline.partitions import partition_week
from betsim.pipeline.resources import MySQLResource, ScraperResource
from betsim.shared.settings import DataSourceConfig
from betsim.shared.utils import get_current_season


def load_existing_gids(mysql: MySQLResource, season: str) -> set[str]:
    df = mysql.query(
        "SELECT DISTINCT gid FROM fixtures WHERE season = :season",
        params={"season": season[-4:]},
    )
    return set(df["gid"].tolist())


def fetch_sources(
    scraper: ScraperResource,
    season: str,
    gid: set[str],
) -> set[str]:
    response = scraper.get(DataSourceConfig.RESULT.format(season))

    soup = BeautifulSoup(response.text, "html.parser")
    pages = [
        page["href"]
        for page in soup.find_all("a", class_="pagenav", href=True)
        if page.text.isnumeric()
    ]
    links = [
        link["href"]
        for link in soup.find_all("a", class_="stat_link", href=True)
    ]

    for page_href in pages:
        response = scraper.get(DataSourceConfig.MATCH.format(page_href))
        soup = BeautifulSoup(response.text, "html.parser")
        links.extend(
            link["href"]
            for link in soup.find_all("a", class_="stat_link", href=True)
        )

    return sorted(
        src for src in set(link.split("/")[-1] for link in links)
        if src.split("-")[-1] not in gid
    )


def scrape_match_page(
    scraper: ScraperResource,
    season: str,
    src: str,
) -> dict[str, str | None]:
    if not (html := load_cache(season, src)):
        html = scraper.get(DataSourceConfig.MATCH.format(src)).text
        write_cache(html, season, src)

    soup = BeautifulSoup(html, "html.parser")

    date = soup.find("div", class_="date_bah")
    home = soup.find("span", class_="homeTeam")
    away = soup.find("span", class_="awayTeam")
    full_goal = soup.find("b", class_="l_scr")
    half_goal = soup.find("span", class_="ht_scr")
    handicap = soup.find("span", class_="forepr ashc")

    return {
        "date": date.text if date else None,
        "home": home.text if home else None,
        "away": away.text if away else None,
        "full_goal": full_goal.text if full_goal else None,
        "half_goal": half_goal.text if half_goal else None,
        "handicap": handicap.text if handicap else None,
        "source": src,
    }


def filter_window(df: pd.DataFrame, window: TimeWindow) -> pd.DataFrame:
    ts = pd.to_datetime(df["date"], format="%d/%m/%Y %H:%M %Z", utc=True)
    return df[(ts >= window.start) & (ts < window.end)]


def scrape_match_pages(
    scraper: ScraperResource,
    season: str,
    srcs: list[str],
    window: TimeWindow,
) -> pd.DataFrame:
    return pd.DataFrame([
        scrape_match_page(scraper, season, src) for src in srcs
    ]).pipe(filter_window, window)


@asset(
    name="match_results",
    description=(
        "Scrapes new J-League match results from Forebet, scoped to "
        "the run's weekly partition."
    ),
    partitions_def=partition_week,
    group_name="Ingestion",
    output_required=False,
    retry_policy=RetryPolicy(max_retries=3, delay=30),
)
def fetch_jleague_results(
    context: AssetExecutionContext,
    mysql: MySQLResource,
    scraper: ScraperResource,
) -> Iterator[Output[pd.DataFrame]]:
    window = context.partition_time_window
    season = get_current_season(window.start)

    gid = load_existing_gids(mysql, season)
    srcs = fetch_sources(scraper, season, gid)

    if not srcs:
        context.log.info(f"No new matches were found for season {season}.")
        return

    df = scrape_match_pages(scraper, season, srcs, window)

    if df.empty:
        context.log.info(
            f"No new matches fell in the partition window "
            f"[{window.start:%Y-%m-%d}, {window.end:%Y-%m-%d})."
        )
        return

    write_artefact(df, "raw/match_results", context.run.run_id)

    context.log.info(f"Found {len(df):,} new matches for season {season}.")

    yield Output(
        df,
        metadata={
            "rows": len(df),
            "season": season,
            "window": [
                f"{window.start:%Y-%m-%d}",
                f"{window.end - timedelta(days=1):%Y-%m-%d}",
            ],
        },
    )
