from sqlalchemy import Column, Double, Integer, MetaData, String, Table

METADATA = MetaData()

fixtures = Table(
    "fixtures",
    METADATA,
    Column("gid", String(64), primary_key=True),
    Column("gdt", String(32)),
    Column("season", Integer),
    Column("date", String(16)),
    Column("home", String(64)),
    Column("away", String(64)),
    Column("hg", Integer),
    Column("ag", Integer),
    Column("res", String(1)),
    Column("hcap_side", String(1)),
    Column("hcap_line", Double),
    Column("hcap_res", String(1)),
)

plays = Table(
    "plays",
    METADATA,
    Column("gid", String(64), primary_key=True),
    Column("season", Integer),
    Column("date", String(16)),
    Column("team", String(64)),
    Column("opponent", String(64)),
    Column("goals", Integer),
    Column("points", Integer),
    Column("net_goals", Integer),
    Column("stadium", Integer),
)

jleague = Table(
    "jleague",
    METADATA,
    Column("gid", String(64), primary_key=True),
    Column("gdt", String(32)),
    Column("season", Integer),
    Column("home", String(64)),
    Column("away", String(64)),
    Column("hcap_res", Double),
    Column("hcap_mag", Double),
    Column("n_rest_day_net", Double),
    Column("rank_net", Double),
    Column("rate_h2h_lose", Double),
    Column("rate_h2h_win", Double),
    Column("rate_seas_lose_net", Double),
    Column("rate_seas_win_net", Double),
    Column("rating_hist_net", Double),
    Column("rating_seas_net", Double),
    Column("scores_net", Double),
    Column("xg_h2h_lose", Double),
    Column("xg_h2h_win", Double),
    Column("xg_net", Double),
    Column("xg_sup", Double),
)

TABLES = {"fixtures": fixtures, "plays": plays, "jleague": jleague}
