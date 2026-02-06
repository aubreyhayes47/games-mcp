import { useMemo } from "react";
import "./app.css";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"];

const STATUS_LABELS = {
  in_progress: "In progress",
  game_over: "Game over",
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

  const board = useMemo(() => parseStateBoard(snapshot?.state), [snapshot?.state]);
  const error = snapshot?.legal === false ? snapshot?.error : null;

  return (
    <GameWidgetShell
      title="Checkers MCP"
      subtitle="Type your move in chat. The board updates only from verified tool results."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="checkers_snapshot"
      isSessionGame={true}
      status={snapshot?.status}
      turn={snapshot?.turn}
      gameId={snapshot?.gameId}
      error={error}
      waitingMessage="Waiting for the next tool update..."
      statusItems={[
        { label: "Status", value: getStatusLabel(snapshot) },
        { label: "Turn", value: getTurnLabel(snapshot?.turn) },
        { label: "Last move", value: snapshot?.lastMove?.notation || "-" },
        { label: "Winner", value: getWinnerLabel(snapshot?.winner) },
      ]}
      instructions={[
        "Type your move in chat (e.g., b6a5 or b6d4f2).",
        "Captures are mandatory when available.",
      ]}
    >
      <section className="board-wrapper">
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
                  className={`square ${isDark ? "square--dark" : "square--light"}`}
                  role="gridcell"
                  aria-label={`Square ${file}${rank}`}
                >
                  {hasPiece ? (
                    <span
                      className={`piece ${isWhite ? "piece--white" : "piece--black"} ${
                        isKing ? "piece--king" : ""
                      }`}
                    />
                  ) : null}
                  <span className="coord">
                    {fileIndex === 0 ? rank : ""}
                    {rankIndex === 7 ? file : ""}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </section>
    </GameWidgetShell>
  );
}
