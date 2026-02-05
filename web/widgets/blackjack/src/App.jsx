import { useEffect, useMemo } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";

const SUIT_SYMBOLS = {
  S: "♠",
  H: "♥",
  D: "♦",
  C: "♣",
};

const STATUS_LABELS = {
  in_progress: "In progress",
  game_over: "Game over",
};

const normalizeToolOutput = (toolOutput) => {
  if (!toolOutput) {
    return null;
  }
  if (toolOutput.structuredContent) {
    return toolOutput.structuredContent;
  }
  return toolOutput;
};

const isSnapshotPayload = (payload) =>
  payload?.type === "blackjack_snapshot" && typeof payload?.state === "string";

const parseState = (state) => {
  if (!state) {
    return {
      dealer: [],
      playerHands: [],
      stack: 0,
      bet: 0,
      turn: "player",
      handIndex: 0,
      status: "in_progress",
      lastAction: null,
      results: [],
    };
  }
  const parts = state.split("|").reduce((acc, chunk) => {
    const separator = chunk.indexOf(":");
    if (separator === -1) {
      return acc;
    }
    const key = chunk.slice(0, separator);
    const value = chunk.slice(separator + 1);
    acc[key] = value;
    return acc;
  }, {});

  const parseList = (value) => {
    if (!value || value === "-") {
      return [];
    }
    return value.split(",").filter(Boolean);
  };

  const parseHands = (value) => {
    if (!value || value === "-") {
      return [];
    }
    return value.split(";").map((chunk) => {
      const [cardsRaw, handState, doubledRaw, betRaw] = chunk.split("@");
      return {
        cards: parseList(cardsRaw),
        state: handState,
        doubled: doubledRaw === "1",
        bet: Number(betRaw || parts.B || 0),
      };
    });
  };

  return {
    dealer: parseList(parts.D),
    playerHands: parseHands(parts.P),
    stack: Number(parts.BK || 0),
    bet: Number(parts.B || 0),
    turn: parts.T || "player",
    handIndex: Number(parts.H || 0),
    status: parts.ST || "in_progress",
    lastAction: parts.LA && parts.LA !== "-" ? parts.LA : null,
    results: parseList(parts.R),
  };
};

const getStatusLabel = (snapshot) => {
  if (!snapshot) {
    return "No game";
  }
  return STATUS_LABELS[snapshot.status] || snapshot.status || "Unknown";
};

const cardLabel = (card) => {
  if (!card || card.length !== 2) {
    return "";
  }
  const rank = card[0];
  const suit = SUIT_SYMBOLS[card[1]] || "";
  return `${rank}${suit}`;
};

const isRedSuit = (card) => {
  if (!card || card.length !== 2) {
    return false;
  }
  return card[1] === "H" || card[1] === "D";
};

const handValue = (cards) => {
  let total = 0;
  let aces = 0;
  const values = {
    A: 11,
    K: 10,
    Q: 10,
    J: 10,
    T: 10,
    "9": 9,
    "8": 8,
    "7": 7,
    "6": 6,
    "5": 5,
    "4": 4,
    "3": 3,
    "2": 2,
  };
  for (const card of cards) {
    const rank = card?.[0];
    total += values[rank] || 0;
    if (rank === "A") {
      aces += 1;
    }
  }
  while (total > 21 && aces > 0) {
    total -= 10;
    aces -= 1;
  }
  return total;
};

const formatChips = (amount) => {
  if (Number.isNaN(amount)) {
    return "0";
  }
  return Number(amount).toFixed(0);
};

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const snapshot = isSnapshotPayload(latestPayload) ? latestPayload : null;

  const isWaitingForTool =
    !isSnapshotPayload(latestPayload) && latestPayload !== null;

  useEffect(() => {
    const handleError = (event) => {
      const message = event?.error?.message || event?.message || "Unknown error";
      // eslint-disable-next-line no-console
      console.error("Widget runtime error:", message, event?.error || event);
    };
    const handleRejection = (event) => {
      const reason = event?.reason;
      // eslint-disable-next-line no-console
      console.error("Widget unhandled rejection:", reason || event);
    };
    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleRejection);
    return () => {
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleRejection);
    };
  }, []);

  const parsedState = useMemo(
    () => parseState(snapshot?.state),
    [snapshot?.state]
  );
  const hideDealerHoleCard =
    snapshot?.turn === "player" && snapshot?.status === "in_progress";
  const visibleDealerCards = hideDealerHoleCard
    ? parsedState.dealer.slice(0, 1)
    : parsedState.dealer;

  return (
    <main className="app">
      <header className="app__header">
        <div>
          <p className="eyebrow">Display-only table</p>
          <h1>Blackjack</h1>
          <p className="app__subtitle">
            Type actions in chat. The table updates only from validated tool output.
          </p>
        </div>
        <div className="table-chip">Actions: hit, stand, double, split</div>
      </header>

      <section className="status" aria-label="Game status">
        <div className="stat-pill">
          <span>Status</span>
          <strong>{getStatusLabel(snapshot)}</strong>
        </div>
        <div className="stat-pill">
          <span>Turn</span>
          <strong>{snapshot?.turn || "-"}</strong>
        </div>
        <div className="stat-pill">
          <span>Stack</span>
          <strong>{formatChips(parsedState.stack)}</strong>
        </div>
        <div className="stat-pill">
          <span>Table Bet</span>
          <strong>{formatChips(parsedState.bet)}</strong>
        </div>
        <div className="stat-pill">
          <span>Last Action</span>
          <strong>{snapshot?.lastAction || "-"}</strong>
        </div>
      </section>

      <section className="table">
        {isWaitingForTool ? (
          <div className="table__waiting" role="status">
            <p>Waiting for the next tool update...</p>
          </div>
        ) : (
          <div className="table__layout">
            <div className="hand-group hand-group--dealer">
              <h2>Dealer</h2>
              <div className="cards cards--dealer">
                {parsedState.dealer.length === 0 ? (
                  <div className="card card--empty">-</div>
                ) : (
                  <>
                    {visibleDealerCards.map((card, idx) => (
                      <div
                        key={`dealer-${card}-${idx}`}
                        className={`card ${isRedSuit(card) ? "card--red" : ""}`}
                      >
                        <span>{cardLabel(card)}</span>
                      </div>
                    ))}
                    {hideDealerHoleCard ? (
                      <div className="card card--hidden" aria-label="Hidden card" />
                    ) : null}
                  </>
                )}
              </div>
              <div className="hand-meta">
                <span>
                  Dealer Total: {hideDealerHoleCard ? "?" : handValue(parsedState.dealer)}
                </span>
              </div>
            </div>

            <div className="hand-group hand-group--player">
              <h2>Player</h2>
              <div className="player-hands">
                {parsedState.playerHands.length === 0 ? (
                  <div className="cards">
                    <div className="card card--empty">-</div>
                  </div>
                ) : (
                  parsedState.playerHands.map((hand, index) => {
                    const isActive =
                      snapshot?.turn === "player" &&
                      parsedState.handIndex === index &&
                      hand.state === "active";
                    return (
                      <article
                        key={`hand-${index}`}
                        className={`player-hand ${
                          isActive ? "player-hand--active" : ""
                        }`}
                      >
                        <p className="player-hand__label">Hand {index + 1}</p>
                        <div className="cards">
                          {hand.cards.map((card, cardIndex) => (
                            <div
                              key={`hand-${index}-${card}-${cardIndex}`}
                              className={`card ${
                                isRedSuit(card) ? "card--red" : ""
                              }`}
                            >
                              <span>{cardLabel(card)}</span>
                            </div>
                          ))}
                        </div>
                        <div className="hand-meta">
                          <span>Total: {handValue(hand.cards)}</span>
                          <span>Bet: {formatChips(hand.bet)}</span>
                          <span>State: {hand.state}</span>
                          <span>Doubled: {hand.doubled ? "Yes" : "No"}</span>
                          {parsedState.results?.[index] ? (
                            <span>Result: {parsedState.results[index]}</span>
                          ) : null}
                        </div>
                      </article>
                    );
                  })
                )}
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="table-meta">
        <span>Dealer hole card remains hidden in chat until reveal conditions are met.</span>
        <p className="table-note">
          Splits and doubles are available when legal; insurance and surrender are disabled.
        </p>
      </section>
    </main>
  );
}
