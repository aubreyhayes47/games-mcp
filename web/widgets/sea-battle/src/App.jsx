import { useMemo } from "react";
import "./app.css";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const FILES = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"];
const RANKS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"];

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
      fogBoard: Array.from({ length: 10 }, () => Array(10).fill(".")),
      opponentFog: Array.from({ length: 10 }, () => Array(10).fill(".")),
      turn: "player",
      status: "in_progress",
      lastAction: "-",
      winner: "-",
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

  return {
    playerBoard: parseBoard(parts.P),
    fogBoard: parseBoard(parts.F),
    opponentFog: parseBoard(parts.OF),
    turn: parts.T || "player",
    status: parts.ST || "in_progress",
    lastAction: parts.LA || "-",
    winner: parts.W || "-",
  };
};

const getShipNeighbors = (board, rowIndex, colIndex) => {
  const up = rowIndex > 0 && board[rowIndex - 1][colIndex] === "S";
  const down = rowIndex < 9 && board[rowIndex + 1][colIndex] === "S";
  const left = colIndex > 0 && board[rowIndex][colIndex - 1] === "S";
  const right = colIndex < 9 && board[rowIndex][colIndex + 1] === "S";
  return { up, down, left, right };
};

const cellClass = (value, showShips, neighbors) => {
  if (value === "H") return "cell cell--hit";
  if (value === "M") return "cell cell--miss";

  if (value === "S" && showShips) {
    const { up, down, left, right } = neighbors || {};
    const shipNeighbors = [up, down, left, right].filter(Boolean).length;
    const classes = ["cell", "cell--ship"];

    if (shipNeighbors <= 1) {
      classes.push("cell--ship-end");
      if (up) classes.push("cell--ship-cap-top");
      if (down) classes.push("cell--ship-cap-bottom");
      if (left) classes.push("cell--ship-cap-left");
      if (right) classes.push("cell--ship-cap-right");
    }

    return classes.join(" ");
  }

  return "cell";
};

const countCells = (board, target) =>
  board.reduce(
    (sum, row) => sum + row.reduce((rowSum, cell) => rowSum + (cell === target ? 1 : 0), 0),
    0
  );

function GridBoard({ board, showShips, title, ariaLabel }) {
  return (
    <div className="board-panel">
      <h2>{title}</h2>
      <div className="board-shell" role="grid" aria-label={ariaLabel}>
        <div className="axis axis--top" aria-hidden="true">
          {FILES.map((file) => (
            <span key={`${title}-file-${file}`}>{file}</span>
          ))}
        </div>

        <div className="board-grid">
          {board.map((row, rowIndex) => (
            <div key={`${title}-row-${rowIndex}`} className="board-row">
              <span className="axis-rank" aria-hidden="true">
                {RANKS[rowIndex]}
              </span>

              {row.map((cell, colIndex) => (
                <div
                  key={`${title}-${rowIndex}-${colIndex}`}
                  className={cellClass(
                    cell,
                    showShips,
                    showShips ? getShipNeighbors(board, rowIndex, colIndex) : null
                  )}
                  role="gridcell"
                  aria-label={`${ariaLabel} ${FILES[colIndex]}${RANKS[rowIndex]}`}
                >
                  {cell === "H" ? <span className="marker">X</span> : null}
                  {cell === "M" ? <span className="marker marker--miss">•</span> : null}
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const snapshot = isSnapshotPayload(latestPayload) ? latestPayload : null;
  const parsedState = useMemo(() => parseState(snapshot?.state), [snapshot?.state]);
  const error = snapshot?.legal === false ? snapshot?.error : null;

  const playerFleetRemaining = countCells(parsedState.playerBoard, "S");
  const enemyHitsOnPlayer = countCells(parsedState.opponentFog, "H");
  const playerHitsOnEnemy = countCells(parsedState.fogBoard, "H");

  return (
    <GameWidgetShell
      title="Sea Battle"
      subtitle="Type coordinates like A1 or J10 in chat. Boards update only from validated tool output."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="sea_battle_snapshot"
      isSessionGame={true}
      status={snapshot?.status}
      turn={snapshot?.turn}
      gameId={snapshot?.gameId}
      error={error}
      waitingMessage="Waiting for the next tool update..."
      statusItems={[
        { label: "Status", value: parsedState.status },
        { label: "Turn", value: parsedState.turn },
        { label: "Last Action", value: parsedState.lastAction },
        { label: "Winner", value: parsedState.winner || "-" },
      ]}
      instructions={[
        `Your Fleet Tiles Remaining: ${playerFleetRemaining}`,
        `Hits Landed: ${playerHitsOnEnemy} | Enemy Hits Landed: ${enemyHitsOnPlayer}`,
      ]}
    >
      <section className="boards">
        <GridBoard
          board={parsedState.playerBoard}
          showShips={true}
          title="Player Fleet"
          ariaLabel="Player board"
        />
        <GridBoard
          board={parsedState.fogBoard}
          showShips={false}
          title="Opponent Waters"
          ariaLabel="Opponent board"
        />
      </section>

      <section className="legend" aria-label="Legend">
        <div><span className="dot dot--ship" /> Ship</div>
        <div><span className="dot dot--hit" /> Hit</div>
        <div><span className="dot dot--miss" /> Miss</div>
      </section>
    </GameWidgetShell>
  );
}
