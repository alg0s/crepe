from __future__ import annotations

from crepe.graph_client import GraphClient


def extract_users(client: GraphClient) -> list[dict]:
    return client.get_paginated("/users", "users")

