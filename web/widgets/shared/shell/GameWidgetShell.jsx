import { useEffect, useMemo, useState } from "react";
import { useDisplayModeController } from "./useDisplayModeController";
import "./shell.css";

function formatAnnouncement({ status, turn, error }) {
  if (error) {
    return `Action rejected: ${error}`;
  }
  if (status === "game_over") {
    return "Game over.";
  }
  if (turn) {
    return `Turn: ${turn}.`;
  }
  if (status) {
    return `Status: ${status}.`;
  }
  return "";
}

export function GameWidgetShell({
  title,
  subtitle,
  latestPayload,
  snapshot,
  snapshotType,
  isSessionGame,
  status,
  turn,
  error,
  gameId,
  waitingMessage,
  statusItems,
  instructions,
  children,
}) {
  const [announcement, setAnnouncement] = useState("");

  const isWaitingForTool = useMemo(() => {
    if (latestPayload === null) {
      return false;
    }
    return !(snapshot && snapshot.type === snapshotType);
  }, [latestPayload, snapshot, snapshotType]);

  useDisplayModeController({
    isSessionGame,
    status,
    gameKey: gameId || `${snapshotType}:${status || "unknown"}`,
  });

  useEffect(() => {
    setAnnouncement(formatAnnouncement({ status, turn, error }));
  }, [error, status, turn]);

  const shellStatusItems = statusItems || [
    { label: "Status", value: status || "-" },
    { label: "Turn", value: turn || "-" },
  ];

  return (
    <main className="app game-shell">
      <div className="game-shell__sr-live" aria-live="polite" aria-atomic="true">
        {announcement}
      </div>

      <header className="game-shell__header">
        <div>
          <h1 className="game-shell__title">{title}</h1>
          {subtitle ? <p className="game-shell__subtitle">{subtitle}</p> : null}
        </div>
      </header>

      {shellStatusItems.length > 0 ? (
        <section className="game-shell__status" aria-label="Game status">
          {shellStatusItems.map((item) => (
            <div key={item.label} className="game-shell__status-item">
              <span className="game-shell__status-item-label">{item.label}</span>
              <strong>{item.value ?? "-"}</strong>
            </div>
          ))}
        </section>
      ) : null}

      {error ? (
        <div className="game-shell__error" role="alert" aria-live="polite">
          {error}
        </div>
      ) : null}

      {isWaitingForTool ? (
        <section className="game-shell__waiting" role="status">
          <p>{waitingMessage || "Waiting for the next tool update..."}</p>
        </section>
      ) : (
        children
      )}

      {instructions?.length ? (
        <section className="game-shell__meta" aria-label="Usage notes">
          {instructions.map((line) => (
            <p key={line}>{line}</p>
          ))}
        </section>
      ) : null}
    </main>
  );
}
