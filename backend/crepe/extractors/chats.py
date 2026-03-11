from __future__ import annotations

from crepe.graph_client import GraphClient


def extract_chats(client: GraphClient) -> list[dict]:
    return client.get_paginated("/chats", "chats")

