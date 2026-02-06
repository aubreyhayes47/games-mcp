import { useMemo } from "react";
import "./app.css";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const COLUMN_LABELS = ["1", "2", "3", "4", "5", "6", "7"];

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
  const parsedState = useMemo(() => parseState(snapshot?.state), [snapshot?.state]);
  const error = snapshot?.legal === false ? snapshot?.error : null;

  return (
    <GameWidgetShell
      title="Four-in-a-Row MCP"
      subtitle="Choose a column (1-7) in chat. The board updates only from tool output."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="four_in_a_row_snapshot"
      isSessionGame={true}
      status={snapshot?.status}
      turn={snapshot?.turn}
      gameId={snapshot?.gameId}
      error={error}
      waitingMessage="Waiting for the next tool update..."
      statusItems={[
        { label: "Status", value: parsedState.status },
        { label: "Turn", value: parsedState.turn },
        { label: "Last", value: parsedState.lastAction },
        { label: "Winner", value: parsedState.winner || "-" },
      ]}
      instructions={[
        "Columns are labeled 1-7 above the board.",
        "Red = player, Yellow = opponent.",
      ]}
    >
      <section className="board-area">
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
      </section>
    </GameWidgetShell>
  );
}
