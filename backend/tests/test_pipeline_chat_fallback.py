from __future__ import annotations

import httpx

from crepe.pipeline import PipelineRunner


class _DummyGraphAuth:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def get_access_token(self) -> str:
        return "token"


class _DummyGraphClient:
    def __init__(self, *_args, **_kwargs) -> None:
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_args) -> None:
        return None


def _app_only_chats_error() -> httpx.HTTPStatusError:
    request = httpx.Request("GET", "https://graph.microsoft.com/v1.0/chats")
    response = httpx.Response(
        400,
        request=request,
        json={"error": {"code": "BadRequest", "message": "Requested API is not supported in application-only context"}},
    )
    return httpx.HTTPStatusError("bad request", request=request, response=response)


def test_run_extract_skips_chats_for_app_only_errors(configured_env, run_db, monkeypatch):
    runner = PipelineRunner(configured_env, run_db)
    chat_message_calls = {"count": 0}
    channel_message_calls = {"count": 0}

    monkeypatch.setattr("crepe.pipeline.GraphAuthenticator", _DummyGraphAuth)
    monkeypatch.setattr("crepe.pipeline.GraphClient", _DummyGraphClient)
    monkeypatch.setattr("crepe.pipeline.extract_users", lambda _client: [{"id": "u1"}])
    monkeypatch.setattr("crepe.pipeline.extract_teams", lambda _client: [{"id": "t1"}])
    monkeypatch.setattr("crepe.pipeline.extract_channels", lambda _client, _teams: [{"id": "c1", "team_id": "t1"}])

    def _raise_chats_error(_client):
        raise _app_only_chats_error()

    monkeypatch.setattr("crepe.pipeline.extract_chats", _raise_chats_error)

    def _track_chat_messages(_client, _chats):
        chat_message_calls["count"] += 1
        return []

    def _track_channel_messages(_client, _channels):
        channel_message_calls["count"] += 1
        return []

    monkeypatch.setattr("crepe.pipeline.extract_chat_messages", _track_chat_messages)
    monkeypatch.setattr("crepe.pipeline.extract_channel_messages", _track_channel_messages)

    run_id = runner.run_extract()

    run = run_db.get_run(run_id)
    assert run is not None
    assert run.status == "completed"
    assert run.stage == "extract"
    assert chat_message_calls["count"] == 0
    assert channel_message_calls["count"] == 1
