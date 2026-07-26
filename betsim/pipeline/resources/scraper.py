import cloudscraper
import requests
from dagster import ConfigurableResource, get_dagster_logger
from pydantic import PrivateAttr


class ScraperResource(ConfigurableResource):
    referer: str
    list_url: str
    max_attempts: int
    min_page_bytes: int
    timeout: int
    proxy_timeout: int

    _candidates: list[str] = PrivateAttr(default_factory=list)
    _cursor: int = PrivateAttr(default=0)
    _proxy: str | None = PrivateAttr(default=None)
    _scraper: cloudscraper.CloudScraper | None = PrivateAttr(default=None)

    def _build(self, proxy: str) -> cloudscraper.CloudScraper:
        scraper = cloudscraper.create_scraper(
            browser={
                "browser": "firefox",
                "platform": "windows",
                "mobile": False,
            },
            delay=10,
        )
        scraper.headers.update({
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": self.referer,
            "Upgrade-Insecure-Requests": "1",
        })
        scraper.proxies = {"http": proxy, "https": proxy}
        return scraper

    def _reset(self) -> None:
        self._candidates = []
        self._cursor = 0
        self._proxy = None
        self._scraper = None

    def _advance(self) -> bool:
        if not self._candidates:
            response = requests.get(self.list_url, timeout=self.timeout)
            response.raise_for_status()
            self._candidates = response.text.split()
        if self._cursor >= min(len(self._candidates), self.max_attempts):
            return False

        self._proxy = self._candidates[self._cursor]
        self._cursor += 1
        self._scraper = self._build(self._proxy)
        return True

    def get(self, url: str) -> requests.Response:
        log = get_dagster_logger()
        if self._scraper is None and not self._advance():
            raise RuntimeError(f"No proxies available to fetch {url}.")

        while True:
            try:
                response = self._scraper.get(url, timeout=self.proxy_timeout)
            except Exception as exc:
                reason = type(exc).__name__
            else:
                if (
                    response.status_code == 200
                    and len(response.text) >= self.min_page_bytes
                ):
                    return response
                reason = (
                    f"HTTP {response.status_code}, "
                    f"{len(response.text)} bytes"
                )

            log.info(f"Rejected {self._proxy} ({reason}).")

            if not self._advance():
                attempts = self._cursor
                self._reset()
                raise RuntimeError(
                    f"No route to {url} after {attempts} proxy attempts."
                )
