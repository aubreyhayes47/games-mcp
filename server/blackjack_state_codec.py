from __future__ import annotations

import json
import os
from functools import lru_cache
import warnings

from cryptography.fernet import Fernet, InvalidToken

try:
    from .blackjack_rules import (
        STATUS_GAME_OVER,
        TURN_DEALER,
        parse_state as parse_blackjack_state,
        serialize_state as serialize_blackjack_state,
    )
except ImportError:  # pragma: no cover - fallback for script execution
    from blackjack_rules import (
        STATUS_GAME_OVER,
        TURN_DEALER,
        parse_state as parse_blackjack_state,
        serialize_state as serialize_blackjack_state,
    )


STATE_TOKEN_VERSION = 1


def encode_public_state(canonical_state_str: str) -> str:
    """Encode canonical blackjack state into a model-visible redacted state string."""
    canonical_state = parse_blackjack_state(canonical_state_str)
    canonical_state_str = serialize_blackjack_state(canonical_state)
    canonical_parts = _parse_segments(canonical_state_str)

    show_full_dealer = (
        canonical_state.turn == TURN_DEALER or canonical_state.status == STATUS_GAME_OVER
    )
    visible_dealer = canonical_state.dealer if show_full_dealer else canonical_state.dealer[:1]

    token_payload = {
        "v": STATE_TOKEN_VERSION,
        "canonical": canonical_state_str,
    }
    token = _fernet().encrypt(json.dumps(token_payload).encode("utf-8")).decode("utf-8")

    return "|".join(
        [
            f"P:{canonical_parts.get('P', '-')}",
            f"D:{_serialize_list(visible_dealer)}",
            f"BK:{canonical_parts.get('BK', '0')}",
            f"B:{canonical_parts.get('B', '0')}",
            f"T:{canonical_parts.get('T', 'player')}",
            f"H:{canonical_parts.get('H', '0')}",
            f"ST:{canonical_parts.get('ST', 'in_progress')}",
            f"LA:{canonical_parts.get('LA', '-')}",
            f"R:{canonical_parts.get('R', '-')}",
            f"X:{token}",
        ]
    )


def decode_public_state(public_state_str: str) -> str:
    """Decode and validate model-visible redacted state into canonical blackjack state."""
    parts = _parse_segments(public_state_str)
    token = parts.get("X")
    if not token:
        raise ValueError("Invalid blackjack state token.")

    try:
        payload_raw = _fernet().decrypt(token.encode("utf-8"))
    except InvalidToken as exc:
        raise ValueError("Invalid blackjack state token.") from exc

    try:
        payload = json.loads(payload_raw.decode("utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid blackjack state token payload.") from exc

    if not isinstance(payload, dict) or payload.get("v") != STATE_TOKEN_VERSION:
        raise ValueError("Invalid blackjack state token payload.")

    canonical_state_str = payload.get("canonical")
    if not isinstance(canonical_state_str, str) or not canonical_state_str.strip():
        raise ValueError("Invalid blackjack state token payload.")

    canonical_state = parse_blackjack_state(canonical_state_str)
    return serialize_blackjack_state(canonical_state)


def _parse_segments(state_str: str) -> dict[str, str]:
    if not isinstance(state_str, str) or not state_str.strip():
        raise ValueError("Invalid blackjack state string.")
    parts: dict[str, str] = {}
    for chunk in state_str.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid blackjack state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value
    return parts


def _serialize_list(values: list[str] | None) -> str:
    if not values:
        return "-"
    return ",".join(values)


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    configured_key = os.getenv("BLACKJACK_STATE_KEY")
    if configured_key:
        try:
            return Fernet(configured_key.encode("utf-8"))
        except Exception as exc:  # noqa: BLE001
            raise ValueError(
                "Invalid BLACKJACK_STATE_KEY; expected Fernet urlsafe-base64 key."
            ) from exc

    warnings.warn(
        "BLACKJACK_STATE_KEY is not set. Using ephemeral process key for blackjack "
        "state tokens.",
        RuntimeWarning,
        stacklevel=2,
    )
    return Fernet(Fernet.generate_key())
