import { useEffect, useMemo } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"];

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
  payload?.type === "checkers_snapshot" && typeof payload?.state === "string";

const parseStateBoard = (state) => {
  if (!state) {
    return Array.from({ length: 8 }, () => Array(8).fill("."));
  }
  const [boardPart] = state.split(" ");
  const rows = boardPart.split("/");
  if (rows.length !== 8) {
    return Array.from({ length: 8 }, () => Array(8).fill("."));
  }
  return rows.map((row) => row.split(""));
};

const getStatusLabel = (snapshot) => {
  if (!snapshot) {
    return "No game";
  }
  return STATUS_LABELS[snapshot.status] || snapshot.status || "Unknown";
};

const getTurnLabel = (turn) => {
  if (turn === "w") return "White";
  if (turn === "b") return "Black";
  return "-";
};

const getWinnerLabel = (winner) => {
  if (winner === "w") return "White";
  if (winner === "b") return "Black";
  return "-";
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

  const board = useMemo(
    () => parseStateBoard(snapshot?.state),
    [snapshot?.state]
  );

  return (
    <main className="app">
      <header className="app__header">
        <div>
          <h1>Checkers MCP</h1>
          <p className="app__subtitle">
            Type your move in chat. The board updates only from verified tool
            results.
          </p>
        </div>
      </header>

      <section className="status">
        <div>
          <strong>Status:</strong> {getStatusLabel(snapshot)}
        </div>
        <div>
          <strong>Turn:</strong> {getTurnLabel(snapshot?.turn)}
        </div>
        <div>
          <strong>Last move:</strong> {snapshot?.lastMove?.notation || "-"}
        </div>
        <div>
          <strong>Winner:</strong> {getWinnerLabel(snapshot?.winner)}
        </div>
      </section>

      <section className="board-wrapper">
        {isWaitingForTool ? (
          <div className="board board--waiting" role="status">
            <p>Waiting for the next tool update...</p>
          </div>
        ) : (
          <div className="board" role="grid" aria-label="Checkers board">
            {RANKS.map((rank, rankIndex) =>
              FILES.map((file, fileIndex) => {
                const piece = board[rankIndex]?.[fileIndex] || ".";
                const isDark = (rankIndex + fileIndex) % 2 === 1;
                const isWhite = piece === "w" || piece === "W";
                const isKing = piece === "W" || piece === "B";
                const hasPiece = piece !== ".";
                return (
                  <div
                    key={`${file}${rank}`}
                    className={`square ${
                      isDark ? "square--dark" : "square--light"
                    }`}
                    role="gridcell"
                    aria-label={`Square ${file}${rank}`}
                  >
                    {hasPiece ? (
                      <span
                        className={`piece ${
                          isWhite ? "piece--white" : "piece--black"
                        } ${isKing ? "piece--king" : ""}`}
                      />
                    ) : null}
                  </div>
                );
              })
            )}
          </div>
        )}
        <div className="board-meta">
          <span>Type your move in chat (e.g., b6a5 or b6d4f2).</span>
          <p className="board-note">Captures are mandatory when available.</p>
          <p className="board-note">Multi-jump captures chain squares together.</p>
        </div>
      </section>
    </main>
  );
}
