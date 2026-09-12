import requests
from dagster import ConfigurableResource, get_dagster_logger


class ScraperResource(ConfigurableResource):
    api_url: str
    api_key: str
    max_attempts: int
    min_page_bytes: int
    timeout: int

    def get(self, url: str) -> requests.Response:
        log = get_dagster_logger()
        for attempt in range(1, self.max_attempts + 1):
            try:
                response = requests.get(
                    self.api_url,
                    params={"apikey": self.api_key, "url": url},
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
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
            log.info(f"Attempt {attempt}/{self.max_attempts} failed ({reason}).")

        raise RuntimeError(
            f"No route to {url} after {self.max_attempts} attempts."
        )
