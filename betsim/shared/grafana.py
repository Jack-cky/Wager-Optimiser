import time

import requests


def push_line_metric(
    url: str,
    user: str,
    token: str,
    measurement: str,
    tags: dict[str, str],
    fields: dict[str, float],
    timeout: float,
) -> requests.Response:
    prefix = measurement
    if tags:
        prefix += "," \
            + ",".join(f"{key}={value}" for key, value in tags.items())
    body = ",".join(f"{key}={value}" for key, value in fields.items())
    payload = f"{prefix} {body} {int(time.time() * 1_000_000_000)}"

    response = requests.post(
        url=url,
        data=payload,
        headers={"Content-Type": "text/plain"},
        auth=(user, token),
        timeout=timeout,
    )
    response.raise_for_status()
    return response
