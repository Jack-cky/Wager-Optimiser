import tomllib
import os

from dotenv import load_dotenv

from betsim.shared.paths import BASE_DIR

load_dotenv(BASE_DIR / "config" / ".env")

with open(BASE_DIR / "config" / "config.toml", "rb") as f:
    TOML = tomllib.load(f)

with open(BASE_DIR / "pyproject.toml", "rb") as f:
    project = tomllib.load(f)["project"]
    SPECS = [
        *project.get("dependencies", []),
        *project.get("optional-dependencies", {}).get("pipeline", []),
    ]


class DatabaseConfig:
    DATABASE = os.getenv("DB_DATABASE")
    HOST = os.getenv("DB_HOST")
    PASSWORD = os.getenv("DB_PASSWORD")
    PORT = int(os.getenv("DB_PORT"))
    USER = os.getenv("DB_USER")


class DatabricksConfig:
    ENDPOINT = os.getenv("DATABRICKS_ENDPOINT_NAME")
    HOST = os.getenv("DATABRICKS_HOST")
    TOKEN = os.getenv("DATABRICKS_TOKEN")


class DataSourceConfig:
    BASE = TOML["data"]["base"]
    MATCH = TOML["data"]["match"]
    RESULT = TOML["data"]["result"]


class GrafanaConfig:
    TOKEN = os.getenv("GRAFANA_TOKEN_WO")
    URL = os.getenv("GRAFANA_URL")
    USER = os.getenv("GRAFANA_USERID")


class MLflowConfig:
    EXPERIMENT = os.getenv("MLFLOW_EXPERIMENT_NAME")
    TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI")

    CATALOG = TOML["mlflow"]["catalog"]
    MODEL = TOML["mlflow"]["model"]
    SCHEMA = TOML["mlflow"]["schema"]
    REGISTRY_URI = TOML["mlflow"]["registry_uri"]


class ModelDependencyConfig:
    PACKAGES = [
        spec for spec in SPECS
        if any(pkg in spec for pkg in TOML["dependency"]["packages"])
    ]


class NetworkConfig:
    HOST = os.getenv("ALLOWED_HOST")
    PORT = TOML["network"]["port"]


class ProxyConfig:
    LIST_URL = TOML["proxy"]["list_url"]
    MAX_ATTEMPTS = TOML["proxy"]["max_attempts"]
    MIN_PAGE_BYTES = TOML["proxy"]["min_page_bytes"]


class ScheduleConfig:
    CRON_SCHEDULE = TOML["schedule"]["cron_schedule"]
    START_FROM = TOML["schedule"]["start_from"]
    TIMEZONE = TOML["schedule"]["timezone"]
    FORMAT_YMD = TOML["schedule"]["format_ymd"]


class SentinelConfig:
    SEASON = TOML["sentinel"]["season"]
    DATE = TOML["sentinel"]["date"]
    DATETIME = TOML["sentinel"]["date"] + " " + TOML["sentinel"]["time"]


class SimulatorConfig:
    PLAYBACK_TIME = TOML["simulator"]["playback_time"]
    RISK_TAKER = TOML["simulator"]["risk_taker"]
    RISK_NEUTRAL = TOML["simulator"]["risk_neutral"]
    RISK_AVERSE = TOML["simulator"]["risk_averse"]


class TimeoutConfig:
    REQUEST = TOML["timeout"]["request"]
    PROXY = TOML["timeout"]["proxy"]
    ENDPOINT_POLL = TOML["timeout"]["endpoint_poll"]
    ENDPOINT_READY = TOML["timeout"]["endpoint_ready"]
