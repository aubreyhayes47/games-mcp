from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from blackjack_rules import BlackjackHand, BlackjackState, serialize_state  # noqa: E402
from blackjack_state_codec import (  # noqa: E402
    decode_public_state,
    encode_public_state,
    _fernet,
)


def _build_canonical_state(*, turn: str, status: str) -> str:
    state = BlackjackState(
        shoe=["2S", "3D", "4H"],
        player_hands=[
            BlackjackHand(cards=["8S", "8D"], state="active", doubled=False, bet=10.0)
        ],
        dealer=["5H", "KD"],
        stack=1000.0,
        bet=10.0,
        turn=turn,
        hand_index=0,
        status=status,
        last_action="deal",
        results=None,
    )
    return serialize_state(state)


def _parts(state: str) -> dict[str, str]:
    return dict(chunk.split(":", 1) for chunk in state.split("|"))


def test_encode_hides_hole_card_on_player_turn(monkeypatch):
    monkeypatch.setenv(
        "BLACKJACK_STATE_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )
    _fernet.cache_clear()
    public_state = encode_public_state(
        _build_canonical_state(turn="player", status="in_progress")
    )
    parts = _parts(public_state)
    assert parts["D"] == "5H"
    assert parts["X"]


def test_encode_reveals_full_dealer_on_dealer_turn(monkeypatch):
    monkeypatch.setenv(
        "BLACKJACK_STATE_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )
    _fernet.cache_clear()
    public_state = encode_public_state(
        _build_canonical_state(turn="dealer", status="in_progress")
    )
    parts = _parts(public_state)
    assert parts["D"] == "5H,KD"


def test_encode_reveals_full_dealer_on_game_over(monkeypatch):
    monkeypatch.setenv(
        "BLACKJACK_STATE_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )
    _fernet.cache_clear()
    public_state = encode_public_state(
        _build_canonical_state(turn="player", status="game_over")
    )
    parts = _parts(public_state)
    assert parts["D"] == "5H,KD"


def test_decode_round_trip(monkeypatch):
    monkeypatch.setenv(
        "BLACKJACK_STATE_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )
    _fernet.cache_clear()
    canonical = _build_canonical_state(turn="player", status="in_progress")
    public_state = encode_public_state(canonical)
    assert decode_public_state(public_state) == canonical


def test_decode_rejects_tampered_token(monkeypatch):
    monkeypatch.setenv(
        "BLACKJACK_STATE_KEY", "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA="
    )
    _fernet.cache_clear()
    canonical = _build_canonical_state(turn="player", status="in_progress")
    public_state = encode_public_state(canonical)
    parts = _parts(public_state)
    token = parts["X"]
    mutated_char = "A" if token[10] != "A" else "B"
    parts["X"] = f"{token[:10]}{mutated_char}{token[11:]}"
    tampered = "|".join(f"{k}:{v}" for k, v in parts.items())
    try:
        decode_public_state(tampered)
        assert False, "expected decode_public_state to reject tampered token"
    except ValueError as exc:
        assert str(exc) == "Invalid blackjack state token."


def test_decode_rejects_missing_token():
    try:
        decode_public_state("P:-|D:-|BK:0|B:0|T:player|H:0|ST:in_progress|LA:-|R:-")
        assert False, "expected decode_public_state to reject missing token"
    except ValueError as exc:
        assert str(exc) == "Invalid blackjack state token."
