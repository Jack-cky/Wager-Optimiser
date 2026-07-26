from betsim.simulator.data import fetch_features, recent_results, team_options
from betsim.shared.utils import get_current_season


def image_path(team: str) -> str:
    team_map = team.lower().replace(" ", "_")
    return f"betsim/simulator/assets/teams/{team_map}.png"


def update_fixture(state, name, value) -> None:
    match name:
        case "team_away":
            state.image_away = image_path(value)
            state.result_away = recent_results(value)
            state.opponent_home = team_options(value)
        case "team_home":
            state.image_home = image_path(value)
            state.result_home = recent_results(value)
            state.opponent_away = team_options(value)

    if state.team_home and state.team_away:
        state.season = get_current_season()

        state.features = fetch_features(
            state.team_home,
            state.team_away,
        )
        data = state.features.round(2).iloc[0]
        state.metric_elo = data["rating_hist_net"]
        state.metric_xg = data["xg_net"]
        state.metric_h2h = data["xg_h2h_win"]
        state.metric_hda = data["rate_h2h_lose"] + data["rate_h2h_win"]

        state.is_fixture = True
