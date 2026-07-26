import json
from time import monotonic, sleep

import pandas as pd
import requests
from taipy.gui import invoke_long_callback

from betsim.simulator.actions.telemetry import track_event
from betsim.shared.settings import DatabricksConfig, SimulatorConfig


def update_bet_readiness(state) -> None:
    state.is_betable = state.hcap_mag is not None \
        and state.risk_attitude is not None


def await_acknowledgement(state) -> None:
    state.is_acknowledge = True
    state.is_transit = False
    state.is_predict = False


def get_risk_threshold(bounds) -> None:
    return f"not {bounds[0]} < pi_hat < {bounds[1]}"


def update_prediction_fields(state) -> None:
    state.is_bet = not state.prediction.query({
        "Taker": get_risk_threshold(SimulatorConfig.RISK_TAKER),
        "Neutral": get_risk_threshold(SimulatorConfig.RISK_NEUTRAL),
        "Averse": get_risk_threshold(SimulatorConfig.RISK_AVERSE),
    }.get(state.risk_attitude, "is_bet")).empty

    data = state.prediction.iloc[0]
    is_home = data["y_hat"] == 1
    state.team_hat = "Home" if is_home else "Away"
    pi_hat = data["pi_hat"] if is_home else 1 - data["pi_hat"]
    state.pi_hat = round(pi_hat * 100)

    result = f"{state.team_hat} team has {state.pi_hat}% chance of " \
        + "covering the spread, "
    team = state.team_home if is_home else state.team_away
    recommend = f"and you should bet on {team}." \
        if state.is_bet else "but you should do nothing."
    state.summary = f"#### {result}{recommend}"


def predict_jleague(df: pd.DataFrame) -> pd.DataFrame:
    url = (
        f"{DatabricksConfig.HOST}/serving-endpoints/"
        f"{DatabricksConfig.ENDPOINT}/invocations"
    )
    headers = {
        "Authorization": f"Bearer {DatabricksConfig.TOKEN}",
        "Content-Type": "application/json",
    }
    payload = json.dumps(
        {"dataframe_split": df.to_dict(orient="split")},
        allow_nan=True,
    )

    response = requests.post(
        url=url,
        headers=headers,
        data=payload,
        timeout=60,
    )
    response.raise_for_status()

    return pd.DataFrame(response.json()["predictions"])


def run_prediction(features, min_seconds: float) -> pd.DataFrame:
    started_at = monotonic()
    prediction = predict_jleague(features)
    elapsed = monotonic() - started_at
    sleep(max(0, min_seconds - elapsed))

    return prediction


def complete_prediction(state, status, prediction=None) -> None:
    state.is_transit = False
    state.is_acknowledge = False

    if status is not True:
        state.is_predict = False
        return

    state.prediction = prediction
    update_prediction_fields(state)
    state.is_predict = True


def predict_result(state, _, payload):
    if payload["args"][0] == 0:
        track_event("prediction")
        state.is_transit = True
        state.features["hcap_mag"] = state.hcap_mag
        invoke_long_callback(
            state,
            run_prediction,
            [state.features.copy(), SimulatorConfig.PLAYBACK_TIME],
            complete_prediction,
        )
        return

    state.is_acknowledge = False


def reset_fixture(state):
    state.is_acknowledge = False
    state.is_betable = False
    state.is_fixture = False
    state.is_predict = False
    state.is_transit = False

    state.team_away = None
    state.team_home = None

    state.hcap_mag = None
    state.risk_attitude = None
