import { useEffect, useMemo } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";

const COLUMN_LABELS = ["A", "B", "C"];
const ROW_LABELS = ["1", "2", "3"];

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
  payload?.type === "tic_tac_toe_snapshot" && typeof payload?.state === "string";

const parseGrid = (raw) => {
  if (!raw) {
    return Array.from({ length: 3 }, () => Array(3).fill("."));
  }
  const rows = raw.split("/");
  if (rows.length !== 3) {
    return Array.from({ length: 3 }, () => Array(3).fill("."));
  }
  return rows.map((row) => row.split(""));
};

const parseState = (state) => {
  if (!state) {
    return {
      grid: Array.from({ length: 3 }, () => Array(3).fill(".")),
      turn: "player",
      status: "in_progress",
      lastAction: "-",
      winner: "-",
      playerSymbol: "X",
      opponentSymbol: "O",
    };
  }
  const parts = state.split("|").reduce((acc, chunk) => {
    const [key, value] = chunk.split(":");
    acc[key] = value;
    return acc;
  }, {});

  return {
    grid: parseGrid(parts.G),
    turn: parts.T || "player",
    status: parts.ST || "in_progress",
    lastAction: parts.LA || "-",
    winner: parts.W || "-",
    playerSymbol: parts.P || "X",
    opponentSymbol: parts.O || "O",
  };
};

const cellClass = (value) => {
  if (value === "X") return "cell cell--x";
  if (value === "O") return "cell cell--o";
  return "cell";
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

  return (
    <main className="app">
      <header className="app__header">
        <div>
          <h1>Tic-Tac-Toe MCP</h1>
          <p className="app__subtitle">
            Type a coordinate like A1, B2, or C3. The board updates only from
            tool output.
          </p>
        </div>
      </header>

      <section className="status">
        <div>
          <strong>Status:</strong> {parsedState.status}
        </div>
        <div>
          <strong>Turn:</strong> {parsedState.turn}
        </div>
        <div>
          <strong>Last:</strong> {parsedState.lastAction}
        </div>
        <div>
          <strong>Winner:</strong> {parsedState.winner || "-"}
        </div>
      </section>

      <section className="board-area">
        {isWaitingForTool ? (
          <div className="board board--waiting" role="status">
            <p>Waiting for the next tool update...</p>
          </div>
        ) : (
          <div className="board-wrapper">
            <div className="column-labels" aria-hidden="true">
              {COLUMN_LABELS.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
            <div className="board" role="grid" aria-label="Tic-Tac-Toe board">
              {parsedState.grid.map((row, rowIndex) =>
                row.map((cell, colIndex) => (
                  <div
                    key={`cell-${rowIndex}-${colIndex}`}
                    className={cellClass(cell)}
                    role="gridcell"
                    aria-label={`${COLUMN_LABELS[colIndex]}${ROW_LABELS[rowIndex]}`}
                  >
                    <span>{cell !== "." ? cell : ""}</span>
                  </div>
                ))
              )}
            </div>
            <div className="row-labels" aria-hidden="true">
              {ROW_LABELS.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
          </div>
        )}
      </section>

      <section className="board-meta">
        <span>Coordinates are A1–C3 with column letters and row numbers.</span>
        <p className="board-note">
          Player symbol: {parsedState.playerSymbol} · Opponent symbol:{" "}
          {parsedState.opponentSymbol}
        </p>
      </section>
    </main>
  );
}
