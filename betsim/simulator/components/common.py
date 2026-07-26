import taipy.gui.builder as tgb


def tgb_header(title: str) -> None:
    with tgb.part():
        tgb.text(title, mode="md")


def tgb_placeholder(placeholder: str = "") -> None:
    with tgb.part():
        tgb.text(placeholder, mode="md")
