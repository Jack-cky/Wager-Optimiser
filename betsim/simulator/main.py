import taipy as tp
import taipy.gui.builder as tgb

from betsim.simulator.actions import (
    await_acknowledgement,
    predict_result,
    reset_fixture,
    track_event,
    update_fixture,
    update_bet_readiness,
)
from betsim.simulator.components import tgb_header, tgb_match, tgb_prediction
from betsim.simulator.state import *
from betsim.shared.settings import NetworkConfig


def on_init(state) -> None:
    track_event("visit")


with tgb.Page() as page:
    with tgb.part("text-center"):
        tgb_header("### JLeague Handicap Results Simulator")
        tgb_match()
        tgb_prediction()


if __name__ == "__main__":
    tp.Gui(page).run(
        host=NetworkConfig.HOST,
        port=NetworkConfig.PORT,
        favicon="assets/icons/favicon.svg",
        title="Bet Simulator",
    )
