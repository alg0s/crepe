from __future__ import annotations

from datetime import timedelta

import pandas as pd


def build_conversations(messages: pd.DataFrame, chat_gap_minutes: int) -> pd.DataFrame:
    """Segment normalized messages into channel threads and chat windows."""

    frames = []
    if messages.empty:
        return pd.DataFrame(
            columns=[
                "conversation_id",
                "source_type",
                "chat_id",
                "team_id",
                "channel_id",
                "start_at",
                "end_at",
                "message_count",
                "participant_count",
                "participants",
                "message_ids",
                "combined_text",
            ]
        )
    if (messages["source_type"] == "channel").any():
        frames.append(_build_channel_conversations(messages[messages["source_type"] == "channel"].copy()))
    if (messages["source_type"] == "chat").any():
        frames.append(_build_chat_conversations(messages[messages["source_type"] == "chat"].copy(), chat_gap_minutes))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _build_channel_conversations(channel_messages: pd.DataFrame) -> pd.DataFrame:
    channel_messages["created_at"] = pd.to_datetime(channel_messages["created_at"], utc=True)
    grouped = channel_messages.groupby(["team_id", "channel_id", "thread_root_id"], dropna=False)
    rows = []
    for (team_id, channel_id, thread_root_id), frame in grouped:
        rows.append(_conversation_row(frame, f"channel:{team_id}:{channel_id}:{thread_root_id}", "channel"))
    return pd.DataFrame(rows)


def _build_chat_conversations(chat_messages: pd.DataFrame, chat_gap_minutes: int) -> pd.DataFrame:
    chat_messages["created_at"] = pd.to_datetime(chat_messages["created_at"], utc=True)
    rows = []
    gap = timedelta(minutes=chat_gap_minutes)
    for chat_id, frame in chat_messages.groupby("chat_id", dropna=False):
        frame = frame.sort_values("created_at").reset_index(drop=True)
        batch_index = 0
        start = 0
        for idx in range(1, len(frame)):
            previous = frame.loc[idx - 1, "created_at"]
            current = frame.loc[idx, "created_at"]
            if current - previous > gap:
                rows.append(_conversation_row(frame.iloc[start:idx], f"chat:{chat_id}:{batch_index}", "chat"))
                batch_index += 1
                start = idx
        rows.append(_conversation_row(frame.iloc[start:], f"chat:{chat_id}:{batch_index}", "chat"))
    return pd.DataFrame(rows)


def _conversation_row(frame: pd.DataFrame, conversation_id: str, source_type: str) -> dict[str, object]:
    ordered = frame.sort_values("created_at")
    participants = sorted({value for value in ordered["sender_id"].dropna().astype(str).tolist() if value})
    return {
        "conversation_id": conversation_id,
        "source_type": source_type,
        "chat_id": ordered["chat_id"].iloc[0] if "chat_id" in ordered else None,
        "team_id": ordered["team_id"].iloc[0] if "team_id" in ordered else None,
        "channel_id": ordered["channel_id"].iloc[0] if "channel_id" in ordered else None,
        "start_at": ordered["created_at"].iloc[0].isoformat(),
        "end_at": ordered["created_at"].iloc[-1].isoformat(),
        "message_count": int(len(ordered)),
        "participant_count": len(participants),
        "participants": "|".join(participants),
        "message_ids": "|".join(ordered["message_id"].astype(str).tolist()),
        "combined_text": " ".join(filter(None, ordered["body_text"].astype(str).tolist())).strip(),
    }

