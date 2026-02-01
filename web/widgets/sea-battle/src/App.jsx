import { useEffect, useMemo } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";

const FILES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
const RANKS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

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
  payload?.type === "sea_battle_snapshot" && typeof payload?.state === "string";

const parseBoard = (raw) => {
  if (!raw) {
    return Array.from({ length: 10 }, () => Array(10).fill("."));
  }
  const rows = raw.split("/");
  if (rows.length !== 10) {
    return Array.from({ length: 10 }, () => Array(10).fill("."));
  }
  return rows.map((row) => row.split(""));
};

const parseState = (state) => {
  if (!state) {
    return {
      playerBoard: Array.from({ length: 10 }, () => Array(10).fill(".")),
      opponentBoard: Array.from({ length: 10 }, () => Array(10).fill(".")),
      fogBoard: Array.from({ length: 10 }, () => Array(10).fill(".")),
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
    playerBoard: parseBoard(parts.P),
    opponentBoard: parseBoard(parts.O),
    fogBoard: parseBoard(parts.F),
    turn: parts.T || "player",
    status: parts.ST || "in_progress",
    lastAction: parts.LA || "-",
    winner: parts.W || "-",
  };
};

const cellClass = (value, showShips) => {
  if (value === "H") return "cell cell--hit";
  if (value === "M") return "cell cell--miss";
  if (value === "S" && showShips) return "cell cell--ship";
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
          <h1>Sea Battle MCP</h1>
          <p className="app__subtitle">
            Type a coordinate like A1 or J10. The boards update only from tool
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

      <section className="boards">
        {isWaitingForTool ? (
          <div className="board board--waiting" role="status">
            <p>Waiting for the next tool update...</p>
          </div>
        ) : (
          <>
            <div className="board-wrapper">
              <h2>Player Fleet</h2>
              <div className="board" role="grid" aria-label="Player board">
                {parsedState.playerBoard.map((row, rowIndex) =>
                  row.map((cell, colIndex) => (
                    <div
                      key={`p-${rowIndex}-${colIndex}`}
                      className={cellClass(cell, true)}
                      role="gridcell"
                      aria-label={`Player ${FILES[colIndex]}${RANKS[rowIndex]}`}
                    />
                  ))
                )}
              </div>
            </div>
            <div className="board-wrapper">
              <h2>Opponent Waters</h2>
              <div className="board" role="grid" aria-label="Opponent board">
                {parsedState.fogBoard.map((row, rowIndex) =>
                  row.map((cell, colIndex) => (
                    <div
                      key={`o-${rowIndex}-${colIndex}`}
                      className={cellClass(cell, false)}
                      role="gridcell"
                      aria-label={`Opponent ${FILES[colIndex]}${RANKS[rowIndex]}`}
                    />
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </section>

      <section className="board-meta">
        <span>Coordinates: A1–J10. Hits and misses are tracked for both sides.</span>
        <p className="board-note">
          The opponent move is selected from a legal list by the model.
        </p>
      </section>
    </main>
  );
}
