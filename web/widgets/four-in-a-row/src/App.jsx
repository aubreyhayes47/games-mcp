import { useEffect, useMemo } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";

const COLUMN_LABELS = ["1", "2", "3", "4", "5", "6", "7"];

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
  payload?.type === "four_in_a_row_snapshot" && typeof payload?.state === "string";

const parseGrid = (raw) => {
  if (!raw) {
    return Array.from({ length: 6 }, () => Array(7).fill("."));
  }
  const rows = raw.split("/");
  if (rows.length !== 6) {
    return Array.from({ length: 6 }, () => Array(7).fill("."));
  }
  return rows.map((row) => row.split(""));
};

const parseState = (state) => {
  if (!state) {
    return {
      grid: Array.from({ length: 6 }, () => Array(7).fill(".")),
      turn: "player",
      status: "in_progress",
      lastAction: "-",
      winner: "-",
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
  };
};

const cellClass = (value) => {
  if (value === "R") return "cell cell--red";
  if (value === "Y") return "cell cell--yellow";
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
          <h1>Four-in-a-Row MCP</h1>
          <p className="app__subtitle">
            Choose a column (1–7) in chat. The board updates only from tool
            output.
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
            <div className="board" role="grid" aria-label="Four-in-a-Row board">
              {parsedState.grid.map((row, rowIndex) =>
                row.map((cell, colIndex) => (
                  <div
                    key={`cell-${rowIndex}-${colIndex}`}
                    className={cellClass(cell)}
                    role="gridcell"
                    aria-label={`Row ${rowIndex + 1}, Col ${colIndex + 1}`}
                  />
                ))
              )}
            </div>
          </div>
        )}
      </section>

      <section className="board-meta">
        <span>Columns are labeled 1–7 above the board.</span>
        <p className="board-note">
          Red = player, Yellow = opponent. Drop tokens by column number.
        </p>
      </section>
    </main>
  );
}
