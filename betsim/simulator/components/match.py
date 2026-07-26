import taipy.gui.builder as tgb

from betsim.simulator.components.common import tgb_placeholder
from betsim.simulator.actions.team import update_fixture


def tgb_team_selector(stadium: str) -> None:
    with tgb.part():
        tgb.selector(
            f"{{team_{stadium}}}",
            label=stadium.title(),
            dropdown=True,
            on_change=update_fixture,
            lov=f"{{opponent_{stadium}}}",
        )


def tgb_team_selection(layout: str = "1 2 4 2 1") -> None:
    with tgb.part():
        with tgb.layout(layout):
            tgb_placeholder()
            tgb_team_selector("home")
            tgb_placeholder()
            tgb_team_selector("away")
            tgb_placeholder()


def tgb_team_image(team: str, width: str = "10vw") -> None:
    with tgb.part(render=f"{{team_{team}}}"):
        tgb.image(f"{{image_{team}}}", width=width)


def tgb_matchup_text() -> None:
    with tgb.part(render="{is_fixture}"):
        tgb.text("#### Matchup", mode="md")
        tgb.text("##### {season}", mode="md")


def tgb_matchup(layout: str = "1 2 4 2 1") -> None:
    with tgb.layout(layout):
        tgb_placeholder()
        tgb_team_image("home")
        tgb_matchup_text()
        tgb_team_image("away")
        tgb_placeholder()


def tgb_team_results(team: str) -> None:
    with tgb.part():
        tgb.text(f"#### {{result_{team}}}", mode="md")


def tgb_recent_results(layout: str = "1 2 4 2 1") -> None:
    with tgb.part(render="{is_fixture}"):
        with tgb.layout(layout):
            tgb_placeholder()
            tgb_team_results("home")
            tgb.text(
                "###### Last 5 Matches (Rightmost is Most Recent)",
                mode="md",
            )
            tgb_team_results("away")
            tgb_placeholder()


def tgb_metrics(layout: str = "1 2 2 2 2 1", height: str = "130px") -> None:
    with tgb.part(render="{is_fixture}"):
        with tgb.layout(layout):
            tgb_placeholder()
            tgb.metric(
                "{metric_elo}",
                type="none",
                title="Elo Rating",
                height=height,
            )
            tgb.metric(
                "{metric_xg}",
                type="none",
                title="xGoals",
                height=height,
            )
            tgb.metric(
                "{metric_h2h}",
                type="circular",
                max=1,
                title="H2H Win Rate",
                height=height,
            )
            tgb.metric(
                "{metric_hda}",
                type="linear",
                min=0,
                max=1,
                title="HDA Result",
                height=height,
            )
            tgb_placeholder()


def tgb_match() -> None:
    with tgb.part():
        tgb_team_selection()
        tgb_matchup()
        tgb_recent_results()
        tgb_metrics()
