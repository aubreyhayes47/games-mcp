from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from blackjack_rules import (  # noqa: E402
    BlackjackHand,
    BlackjackState,
    apply_blackjack_action,
    hand_value,
    legal_dealer_actions,
    legal_player_actions,
    parse_state,
    resolve_results,
    serialize_state,
)


def build_state(
    *,
    shoe,
    player_hands,
    dealer,
    stack=1000.0,
    bet=10.0,
    turn="player",
    hand_index=0,
    status="in_progress",
):
    state = BlackjackState(
        shoe=shoe,
        player_hands=player_hands,
        dealer=dealer,
        stack=stack,
        bet=bet,
        turn=turn,
        hand_index=hand_index,
        status=status,
        last_action=None,
        results=None,
    )
    return serialize_state(state)


def test_hand_value_soft_ace():
    total, is_soft = hand_value(["AS", "6D"])
    assert total == 17
    assert is_soft

    total, is_soft = hand_value(["AS", "AD", "9H"])
    assert total == 21
    assert is_soft


def test_legal_player_actions_include_split_and_double():
    state_str = build_state(
        shoe=["2S", "3D"],
        player_hands=[
            BlackjackHand(cards=["8S", "8D"], state="active", doubled=False, bet=10.0)
        ],
        dealer=["5H", "KD"],
    )
    state = parse_state(state_str)
    actions = legal_player_actions(state)
    assert "hit" in actions
    assert "stand" in actions
    assert "double" in actions
    assert "split" in actions


def test_apply_hit_bust_advances_turn():
    state_str = build_state(
        shoe=["5H"],
        player_hands=[
            BlackjackHand(cards=["TS", "9D"], state="active", doubled=False, bet=10.0)
        ],
        dealer=["7C", "8C"],
    )
    result = apply_blackjack_action(state_str, "hit")
    assert result["legal"] is True
    parsed = parse_state(result["state"])
    assert parsed.player_hands[0].state == "bust"
    assert parsed.turn == "dealer"


def test_apply_split_creates_two_hands():
    state_str = build_state(
        shoe=["2S", "3D"],
        player_hands=[
            BlackjackHand(cards=["8S", "8D"], state="active", doubled=False, bet=10.0)
        ],
        dealer=["5H", "KD"],
    )
    result = apply_blackjack_action(state_str, "split")
    assert result["legal"] is True
    parsed = parse_state(result["state"])
    assert len(parsed.player_hands) == 2
    assert len(parsed.player_hands[0].cards) == 2
    assert len(parsed.player_hands[1].cards) == 2
    assert parsed.hand_index == 0


def test_apply_double_stands_hand():
    state_str = build_state(
        shoe=["5H"],
        player_hands=[
            BlackjackHand(cards=["5S", "6D"], state="active", doubled=False, bet=10.0)
        ],
        dealer=["7C", "8C"],
    )
    result = apply_blackjack_action(state_str, "double")
    assert result["legal"] is True
    parsed = parse_state(result["state"])
    assert parsed.player_hands[0].doubled is True
    assert parsed.player_hands[0].state in {"stood", "bust"}
    assert parsed.turn == "dealer"


def test_legal_dealer_actions_soft_17_stands():
    state_str = build_state(
        shoe=["2S"],
        player_hands=[
            BlackjackHand(cards=["9S", "8D"], state="stood", doubled=False, bet=10.0)
        ],
        dealer=["AS", "6D"],
        turn="dealer",
    )
    state = parse_state(state_str)
    actions = legal_dealer_actions(state)
    assert actions == ["stand"]


def test_resolve_results_dealer_bust():
    state_str = build_state(
        shoe=[],
        player_hands=[
            BlackjackHand(cards=["9S", "8D"], state="stood", doubled=False, bet=10.0)
        ],
        dealer=["TS", "8C", "6H"],
        turn="dealer",
        status="game_over",
    )
    state = parse_state(state_str)
    results = resolve_results(state)
    assert results == ["win"]


def test_double_not_allowed_when_stack_insufficient():
    state_str = build_state(
        shoe=["2S"],
        player_hands=[
            BlackjackHand(cards=["9S", "8D"], state="active", doubled=False, bet=10.0)
        ],
        dealer=["AS", "6D"],
        stack=10.0,
        bet=10.0,
    )
    state = parse_state(state_str)
    actions = legal_player_actions(state)
    assert "double" not in actions


def test_blackjack_payout_updates_stack():
    state_str = build_state(
        shoe=[],
        player_hands=[
            BlackjackHand(cards=["AS", "KD"], state="stood", doubled=False, bet=10.0)
        ],
        dealer=["TS", "7D"],
        stack=100.0,
        bet=10.0,
        turn="dealer",
        status="in_progress",
    )
    result = apply_blackjack_action(state_str, "stand")
    assert result["legal"] is True
    parsed = parse_state(result["state"])
    assert parsed.status == "game_over"
    assert parsed.stack == 115.0
