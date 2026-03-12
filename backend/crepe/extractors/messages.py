from __future__ import annotations

from crepe.graph_client import GraphClient


def extract_chat_messages(client: GraphClient, chats: list[dict]) -> list[dict]:
    messages: list[dict] = []
    for chat in chats:
        chat_id = chat["id"]
        messages.extend(
            client.get_paginated(
                f"/chats/{chat_id}/messages",
                "chat_messages",
                context={"chat_id": chat_id},
            )
        )
    return messages


def extract_channel_messages(client: GraphClient, channels: list[dict]) -> list[dict]:
    messages: list[dict] = []
    for channel in channels:
        team_id = channel.get("team_id")
        channel_id = channel["id"]
        if not team_id:
            continue
        messages.extend(
            client.get_paginated(
                f"/teams/{team_id}/channels/{channel_id}/messages",
                "channel_messages",
                context={"team_id": team_id, "channel_id": channel_id},
            )
        )
    return messages
