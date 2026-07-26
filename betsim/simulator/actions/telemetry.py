import threading

from betsim.shared.grafana import push_line_metric
from betsim.shared.settings import GrafanaConfig, TimeoutConfig

MEASUREMENT = "simulator_event"


def _push(event: str) -> None:
    try:
        push_line_metric(
            GrafanaConfig.URL,
            GrafanaConfig.USER,
            GrafanaConfig.TOKEN,
            MEASUREMENT,
            {"type": event},
            {"value": 1},
            TimeoutConfig.REQUEST,
        )
    except Exception:
        pass


def track_event(event: str) -> None:
    if not GrafanaConfig.URL:
        return
    threading.Thread(target=_push, args=(event,), daemon=True).start()
