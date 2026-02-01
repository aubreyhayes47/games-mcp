from __future__ import annotations

from dataclasses import dataclass
import random


RANKS = "A23456789TJQK"
SUITS = "SHDC"
CARD_VALUES = {
    "A": 11,
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "T": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
}

MAX_HANDS = 4
STATUS_IN_PROGRESS = "in_progress"
STATUS_GAME_OVER = "game_over"
TURN_PLAYER = "player"
TURN_DEALER = "dealer"


@dataclass
class BlackjackHand:
    cards: list[str]
    state: str
    doubled: bool


@dataclass
class BlackjackState:
    shoe: list[str]
    player_hands: list[BlackjackHand]
    dealer: list[str]
    turn: str
    hand_index: int
    status: str
    last_action: str | None = None
    results: list[str] | None = None


def new_shoe(rng: random.Random | None = None) -> list[str]:
    cards = [rank + suit for rank in RANKS for suit in SUITS]
    rng = rng or random.Random()
    rng.shuffle(cards)
    return cards


def serialize_state(state: BlackjackState) -> str:
    return "|".join(
        [
            f"S:{_serialize_list(state.shoe)}",
            f"P:{_serialize_hands(state.player_hands)}",
            f"D:{_serialize_list(state.dealer)}",
            f"T:{state.turn}",
            f"H:{state.hand_index}",
            f"ST:{state.status}",
            f"LA:{state.last_action or '-'}",
            f"R:{_serialize_list(state.results) if state.results else '-'}",
        ]
    )


def parse_state(state_str: str) -> BlackjackState:
    if not isinstance(state_str, str) or not state_str.strip():
        raise ValueError("Invalid blackjack state string.")
    parts: dict[str, str] = {}
    for chunk in state_str.split("|"):
        if ":" not in chunk:
            raise ValueError("Invalid blackjack state segment.")
        key, value = chunk.split(":", 1)
        parts[key] = value
    shoe = _parse_list(parts.get("S"))
    player_hands = _parse_hands(parts.get("P"))
    dealer = _parse_list(parts.get("D"))
    turn = parts.get("T") or TURN_PLAYER
    hand_index_raw = parts.get("H")
    status = parts.get("ST") or STATUS_IN_PROGRESS
    last_action = parts.get("LA") or None
    results = _parse_list(parts.get("R")) if parts.get("R") not in (None, "-") else None

    if turn not in {TURN_PLAYER, TURN_DEALER}:
        raise ValueError("Invalid blackjack turn.")
    try:
        hand_index = int(hand_index_raw) if hand_index_raw is not None else 0
    except ValueError as exc:
        raise ValueError("Invalid blackjack hand index.") from exc
    if status not in {STATUS_IN_PROGRESS, STATUS_GAME_OVER}:
        raise ValueError("Invalid blackjack status.")
    if hand_index < 0:
        raise ValueError("Invalid blackjack hand index.")

    _validate_cards(shoe)
    _validate_cards(dealer)
    for hand in player_hands:
        _validate_cards(hand.cards)

    return BlackjackState(
        shoe=shoe,
        player_hands=player_hands,
        dealer=dealer,
        turn=turn,
        hand_index=hand_index,
        status=status,
        last_action=None if last_action == "-" else last_action,
        results=results,
    )


def initial_blackjack_state(rng: random.Random | None = None) -> BlackjackState:
    shoe = new_shoe(rng)
    player_hand = BlackjackHand(
        cards=[_draw(shoe), _draw(shoe)], state="active", doubled=False
    )
    dealer = [_draw(shoe), _draw(shoe)]

    status = STATUS_IN_PROGRESS
    if _is_blackjack(player_hand.cards) or _is_blackjack(dealer):
        status = STATUS_GAME_OVER

    state = BlackjackState(
        shoe=shoe,
        player_hands=[player_hand],
        dealer=dealer,
        turn=TURN_PLAYER,
        hand_index=0,
        status=status,
        last_action="deal",
    )
    if status == STATUS_GAME_OVER:
        state.results = resolve_results(state)
    return state


def legal_player_actions(state: BlackjackState) -> list[str]:
    if state.status != STATUS_IN_PROGRESS or state.turn != TURN_PLAYER:
        return []
    hand = _current_hand(state)
    if hand is None or hand.state != "active":
        return []
    actions = ["hit", "stand"]
    if _can_double(hand):
        actions.append("double")
    if _can_split(state, hand):
        actions.append("split")
    return actions


def legal_dealer_actions(state: BlackjackState) -> list[str]:
    if state.status != STATUS_IN_PROGRESS or state.turn != TURN_DEALER:
        return []
    total, is_soft = hand_value(state.dealer)
    if total < 17:
        return ["hit"]
    if total == 17 and not is_soft:
        return ["stand"]
    if total == 17 and is_soft:
        return ["stand"]
    return ["stand"]


def apply_blackjack_action(state_str: str, action: str) -> dict[str, object]:
    try:
        state = parse_state(state_str)
    except ValueError as exc:
        return {
            "legal": False,
            "state": state_str,
            "error": str(exc),
        }

    normalized_action = (action or "").strip().lower()
    if not normalized_action:
        return _illegal(state, "Invalid action.")
    if state.status != STATUS_IN_PROGRESS:
        return _illegal(state, "Game is already over.")

    if state.turn == TURN_PLAYER:
        if normalized_action not in legal_player_actions(state):
            return _illegal(state, "Illegal action.")
        _apply_player_action(state, normalized_action)
    else:
        if normalized_action not in legal_dealer_actions(state):
            return _illegal(state, "Illegal action.")
        _apply_dealer_action(state, normalized_action)

    state.last_action = normalized_action
    return {
        "legal": True,
        "state": serialize_state(state),
        "status": state.status,
        "turn": state.turn,
        "lastAction": state.last_action,
        "results": state.results,
        "handIndex": state.hand_index,
    }


def resolve_results(state: BlackjackState) -> list[str]:
    dealer_total, _ = hand_value(state.dealer)
    dealer_blackjack = _is_blackjack(state.dealer)
    dealer_bust = dealer_total > 21
    results = []

    for hand in state.player_hands:
        total, _ = hand_value(hand.cards)
        if hand.state == "bust" or total > 21:
            results.append("bust")
            continue
        if _is_blackjack(hand.cards) and not dealer_blackjack:
            results.append("blackjack")
            continue
        if dealer_blackjack and _is_blackjack(hand.cards):
            results.append("push")
            continue
        if dealer_blackjack:
            results.append("lose")
            continue
        if dealer_bust:
            results.append("win")
            continue
        if total > dealer_total:
            results.append("win")
        elif total < dealer_total:
            results.append("lose")
        else:
            results.append("push")
    return results


def _apply_player_action(state: BlackjackState, action: str) -> None:
    hand = _current_hand(state)
    if hand is None:
        state.turn = TURN_DEALER
        return

    if action == "hit":
        hand.cards.append(_draw(state.shoe))
        total, _ = hand_value(hand.cards)
        if total > 21:
            hand.state = "bust"
            _advance_player_turn(state)
        elif total == 21:
            hand.state = "stood"
            _advance_player_turn(state)
        return

    if action == "stand":
        hand.state = "stood"
        _advance_player_turn(state)
        return

    if action == "double":
        hand.cards.append(_draw(state.shoe))
        hand.doubled = True
        total, _ = hand_value(hand.cards)
        if total > 21:
            hand.state = "bust"
        else:
            hand.state = "stood"
        _advance_player_turn(state)
        return

    if action == "split":
        _apply_split(state, hand)
        return


def _apply_dealer_action(state: BlackjackState, action: str) -> None:
    if action == "hit":
        state.dealer.append(_draw(state.shoe))
        if hand_value(state.dealer)[0] > 21:
            state.status = STATUS_GAME_OVER
            state.results = resolve_results(state)
        return

    if action == "stand":
        state.status = STATUS_GAME_OVER
        state.results = resolve_results(state)


def _apply_split(state: BlackjackState, hand: BlackjackHand) -> None:
    if len(state.player_hands) >= MAX_HANDS:
        return
    left_card, right_card = hand.cards
    hand.cards = [left_card, _draw(state.shoe)]
    hand.state = "active"
    hand.doubled = False
    new_hand = BlackjackHand(
        cards=[right_card, _draw(state.shoe)], state="active", doubled=False
    )
    state.player_hands.insert(state.hand_index + 1, new_hand)


def _advance_player_turn(state: BlackjackState) -> None:
    while state.hand_index < len(state.player_hands):
        if state.player_hands[state.hand_index].state == "active":
            return
        state.hand_index += 1

    if state.player_hands and all(hand.state == "bust" for hand in state.player_hands):
        state.turn = TURN_DEALER
        state.status = STATUS_GAME_OVER
        state.results = resolve_results(state)
        return

    state.turn = TURN_DEALER
    state.hand_index = max(0, min(state.hand_index, len(state.player_hands) - 1))
    if _is_blackjack(state.dealer):
        state.status = STATUS_GAME_OVER
        state.results = resolve_results(state)


def _current_hand(state: BlackjackState) -> BlackjackHand | None:
    if not state.player_hands:
        return None
    if state.hand_index < 0 or state.hand_index >= len(state.player_hands):
        return None
    return state.player_hands[state.hand_index]


def _can_double(hand: BlackjackHand) -> bool:
    return len(hand.cards) == 2 and hand.state == "active"


def _can_split(state: BlackjackState, hand: BlackjackHand) -> bool:
    if len(hand.cards) != 2 or hand.state != "active":
        return False
    if len(state.player_hands) >= MAX_HANDS:
        return False
    return _card_rank(hand.cards[0]) == _card_rank(hand.cards[1])


def _is_blackjack(cards: list[str]) -> bool:
    if len(cards) != 2:
        return False
    return hand_value(cards)[0] == 21


def hand_value(cards: list[str]) -> tuple[int, bool]:
    total = 0
    aces = 0
    for card in cards:
        rank = _card_rank(card)
        total += CARD_VALUES[rank]
        if rank == "A":
            aces += 1
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total, aces > 0


def _draw(shoe: list[str]) -> str:
    if not shoe:
        raise ValueError("Shoe is empty.")
    return shoe.pop(0)


def _serialize_list(values: list[str] | None) -> str:
    if not values:
        return "-"
    return ",".join(values)


def _parse_list(raw: str | None) -> list[str]:
    if not raw or raw == "-":
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _serialize_hands(hands: list[BlackjackHand]) -> str:
    if not hands:
        return "-"
    chunks = []
    for hand in hands:
        cards = _serialize_list(hand.cards)
        chunks.append(f"{cards}@{hand.state}@{1 if hand.doubled else 0}")
    return ";".join(chunks)


def _parse_hands(raw: str | None) -> list[BlackjackHand]:
    if not raw or raw == "-":
        return []
    hands: list[BlackjackHand] = []
    for chunk in raw.split(";"):
        if not chunk:
            continue
        parts = chunk.split("@")
        if len(parts) != 3:
            raise ValueError("Invalid blackjack hand format.")
        cards = _parse_list(parts[0])
        state = parts[1]
        doubled = parts[2] == "1"
        if state not in {"active", "stood", "bust", "blackjack"}:
            raise ValueError("Invalid blackjack hand state.")
        hands.append(BlackjackHand(cards=cards, state=state, doubled=doubled))
    return hands


def _card_rank(card: str) -> str:
    if not card or len(card) != 2:
        raise ValueError("Invalid card format.")
    rank = card[0]
    if rank not in RANKS:
        raise ValueError("Invalid card rank.")
    return rank


def _validate_cards(cards: list[str]) -> None:
    for card in cards:
        if len(card) != 2:
            raise ValueError("Invalid card format.")
        rank = card[0]
        suit = card[1]
        if rank not in RANKS or suit not in SUITS:
            raise ValueError("Invalid card in state.")


def _illegal(state: BlackjackState, message: str) -> dict[str, object]:
    return {
        "legal": False,
        "state": serialize_state(state),
        "error": message,
    }
