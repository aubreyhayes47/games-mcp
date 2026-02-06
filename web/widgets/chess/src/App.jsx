import { useMemo } from "react";
import "./app.css";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const FILES = ["a", "b", "c", "d", "e", "f", "g", "h"];
const RANKS = ["8", "7", "6", "5", "4", "3", "2", "1"];
const PIECES = {
  p: "♟",
  r: "♜",
  n: "♞",
  b: "♝",
  q: "♛",
  k: "♚",
  P: "♙",
  R: "♖",
  N: "♘",
  B: "♗",
  Q: "♕",
  K: "♔",
};

const STATUS_LABELS = {
  in_progress: "In progress",
  check: "Check",
  checkmate: "Checkmate",
  stalemate: "Stalemate",
  game_over: "Game over",
};

const isSnapshotPayload = (payload) =>
  payload?.type === "chess_snapshot" && typeof payload?.fen === "string";

const parseFenBoard = (fen) => {
  if (!fen) {
    return Array.from({ length: 8 }, () => Array(8).fill(null));
  }
  const [boardPart] = fen.split(" ");
  const rows = boardPart.split("/");
  return rows.map((row) => {
    const squares = [];
    for (const char of row) {
      const count = Number(char);
      if (Number.isInteger(count) && count > 0) {
        for (let i = 0; i < count; i += 1) {
          squares.push(null);
        }
      } else {
        squares.push(char);
      }
    }
    return squares;
  });
};

const squareToIndices = (square) => {
  const file = square[0];
  const rank = square[1];
  return {
    fileIndex: FILES.indexOf(file),
    rankIndex: RANKS.indexOf(rank),
  };
};

const getPieceAtSquare = (board, square) => {
  const { fileIndex, rankIndex } = squareToIndices(square);
  if (rankIndex < 0 || fileIndex < 0) {
    return null;
  }
  return board[rankIndex]?.[fileIndex] ?? null;
};

const getStatusLabel = (snapshot) => {
  if (!snapshot) {
    return "No game";
  }
  return STATUS_LABELS[snapshot.status] || snapshot.status || "Unknown";
};

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const snapshot = isSnapshotPayload(latestPayload) ? latestPayload : null;

  const board = useMemo(() => parseFenBoard(snapshot?.fen), [snapshot?.fen]);
  const error = snapshot?.legal === false ? snapshot?.error : null;

  return (
    <GameWidgetShell
      title="Chess MCP"
      subtitle="Type your move in chat. The board updates only from verified tool results."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="chess_snapshot"
      isSessionGame={true}
      status={snapshot?.status}
      turn={snapshot?.turn}
      gameId={snapshot?.gameId}
      error={error}
      waitingMessage="Waiting for the next tool update..."
      statusItems={[
        { label: "Status", value: getStatusLabel(snapshot) },
        { label: "Turn", value: snapshot?.turn || "-" },
        {
          label: "Last move",
          value: snapshot?.lastMove?.san || snapshot?.lastMove?.uci || "-",
        },
        { label: "Check", value: snapshot?.check ? "Yes" : "No" },
      ]}
      instructions={[
        "Type your move in chat (UCI like e2e4 or SAN like Nf3).",
        "For promotions, include the piece letter (e.g., e7e8q).",
      ]}
    >
      <section className="board-wrapper">
        <div className="board" role="grid" aria-label="Chess board">
          {RANKS.map((rank, rankIndex) =>
            FILES.map((file, fileIndex) => {
              const square = `${file}${rank}`;
              const piece = getPieceAtSquare(board, square);
              const isDark = (rankIndex + fileIndex) % 2 === 1;
              return (
                <div
                  key={square}
                  className={`square ${isDark ? "square--dark" : "square--light"}`}
                  role="gridcell"
                  aria-label={`Square ${square}`}
                >
                  <span className="piece">{piece ? PIECES[piece] : ""}</span>
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
