import { useMemo } from "react";
import "./app.css";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const COLUMN_LABELS = ["A", "B", "C"];
const ROW_LABELS = ["1", "2", "3"];

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
  const parsedState = useMemo(() => parseState(snapshot?.state), [snapshot?.state]);
  const error = snapshot?.legal === false ? snapshot?.error : null;

  return (
    <GameWidgetShell
      title="Tic-Tac-Toe Notebook"
      subtitle="Type a coordinate like A1, B2, or C3. The board updates from tool output."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="tic_tac_toe_snapshot"
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
        "Coordinates are A1-C3.",
        `Player: ${parsedState.playerSymbol} | Opponent: ${parsedState.opponentSymbol}`,
      ]}
    >
      <section className="board-area">
        <div className="board-sheet">
          <div className="board-wrapper">
            <span className="axis-corner" aria-hidden="true" />
            <div className="column-labels" aria-hidden="true">
              {COLUMN_LABELS.map((label) => (
                <span key={label}>{label}</span>
              ))}
            </div>
            <div className="row-labels" aria-hidden="true">
              {ROW_LABELS.map((label) => (
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
          </div>
        </div>
      </section>
    </GameWidgetShell>
  );
}
