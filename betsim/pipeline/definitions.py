from dagster import (
    Definitions,
    load_asset_checks_from_modules,
    load_assets_from_modules,
)

from . import checks
from .assets import (
    cleansing,
    deployment,
    engineering,
    ingestion,
    monitoring,
    publishing,
    training,
)
from .resources import (
    DatabricksResource,
    GrafanaResource,
    MlflowResource,
    MySQLResource,
    ScraperResource,
)
from .schedules import (
    betsim_data_job,
    betsim_ml_job,
    betsim_weekly_job,
    betsim_weekly_schedule,
)
from betsim.shared.settings import (
    DatabaseConfig,
    DatabricksConfig,
    GrafanaConfig,
    MLflowConfig,
    ModelDependencyConfig,
    ScraperConfig,
    TimeoutConfig,
)


all_assets = load_assets_from_modules(
    [
        ingestion,
        cleansing,
        engineering,
        publishing,
        monitoring,
        training,
        deployment,
    ],
)

resources = {
    "databricks": DatabricksResource(
        endpoint=DatabricksConfig.ENDPOINT,
        host=DatabricksConfig.HOST,
        token=DatabricksConfig.TOKEN,
    ),
    "mlflow": MlflowResource(
        catalog=MLflowConfig.CATALOG,
        dependencies=ModelDependencyConfig.PACKAGES,
        experiment=MLflowConfig.EXPERIMENT,
        registry_uri=MLflowConfig.REGISTRY_URI,
        tracking_uri=MLflowConfig.TRACKING_URI,
        uc_schema=MLflowConfig.SCHEMA,
    ),
    "mysql": MySQLResource(
        user=DatabaseConfig.USER,
        password=DatabaseConfig.PASSWORD,
        host=DatabaseConfig.HOST,
        port=DatabaseConfig.PORT,
        database=DatabaseConfig.DATABASE,
    ),
    "grafana": GrafanaResource(
        token=GrafanaConfig.TOKEN,
        url=GrafanaConfig.URL,
        user=GrafanaConfig.USER,
    ),
    "scraper": ScraperResource(
        api_url=ScraperConfig.API_URL,
        api_key=ScraperConfig.API_KEY,
        max_attempts=ScraperConfig.MAX_ATTEMPTS,
        min_page_bytes=ScraperConfig.MIN_PAGE_BYTES,
        timeout=TimeoutConfig.SCRAPER,
    ),
}


defs = Definitions(
    assets=all_assets,
    asset_checks=load_asset_checks_from_modules([checks]),
    jobs=[betsim_data_job, betsim_ml_job, betsim_weekly_job],
    schedules=[betsim_weekly_schedule],
    resources=resources,
)
