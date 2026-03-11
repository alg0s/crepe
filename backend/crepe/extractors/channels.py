from __future__ import annotations

from crepe.graph_client import GraphClient


def extract_channels(client: GraphClient, teams: list[dict]) -> list[dict]:
    channels: list[dict] = []
    for team in teams:
        team_id = team["id"]
        fetched = client.get_paginated(
            f"/teams/{team_id}/channels",
            "channels",
            context={"team_id": team_id},
        )
        channels.extend([{**channel, "team_id": team_id} for channel in fetched])
    return channels
