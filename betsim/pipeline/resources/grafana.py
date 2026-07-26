import requests
from dagster import ConfigurableResource, get_dagster_logger

from betsim.shared.grafana import push_line_metric
from betsim.shared.settings import TimeoutConfig


class GrafanaResource(ConfigurableResource):
    token: str
    url: str
    user: str

    def push_metric(
        self,
        measurement: str,
        stage: str,
        field: str,
        value: float,
    ) -> None:
        log = get_dagster_logger()
        try:
            push_line_metric(
                self.url,
                self.user,
                self.token,
                measurement,
                {"stage": stage},
                {field: value},
                TimeoutConfig.REQUEST,
            )
            log.info(
                f"Successfully pushed metric '{measurement}' with "
                f"{field}: {value} to Grafana Cloud."
            )
        except requests.HTTPError as exc:
            log.error(
                f"Failed to push metrics ({exc.response.status_code}): "
                f"{exc.response.text}."
            )
        except requests.RequestException:
            log.error("Failed to connect to Grafana Cloud.")
