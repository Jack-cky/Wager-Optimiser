from .data import team_options


# default UI state
is_acknowledge = is_betable = is_fixture = is_predict = is_transit = False


# default match state
season = None


# default team state
team_away = team_home = None
image_away = image_home = None
opponent_away = opponent_home = team_options(None)
result_away = result_home = None


# default metrics state
features = None
metric_elo = metric_xg = metric_hda = metric_h2h = None


# default bet state
hcap_mag = risk_attitude = None
option_risk = ["Default", "Averse", "Neutral", "Taker"]


# default prediction state
prediction = None
is_bet = pi_hat = team_hat = None
summary = None
