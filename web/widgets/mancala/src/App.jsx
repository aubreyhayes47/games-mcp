import { useMemo } from "react";
import "./app.css";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const PIT_LABELS = ["1", "2", "3", "4", "5", "6"];

const isSnapshotPayload = (payload) =>
  payload?.type === "mancala_snapshot" && typeof payload?.state === "string";

const parsePitRow = (raw) => {
  if (!raw) {
    return [0, 0, 0, 0, 0, 0];
  }
  const values = raw.split(",").map((value) => Number.parseInt(value, 10));
  if (values.length !== 6 || values.some((value) => !Number.isFinite(value) || value < 0)) {
    return [0, 0, 0, 0, 0, 0];
  }
  return values;
};

const parseState = (state) => {
  if (!state) {
    return {
      playerPits: [0, 0, 0, 0, 0, 0],
      opponentPits: [0, 0, 0, 0, 0, 0],
      playerStore: 0,
      opponentStore: 0,
      turn: "player",
      status: "in_progress",
      lastAction: "-",
      winner: "-",
    };
  }

  const parts = state.split("|").reduce((acc, chunk) => {
    const separator = chunk.indexOf(":");
    if (separator <= 0) {
      return acc;
    }
    const key = chunk.slice(0, separator);
    const value = chunk.slice(separator + 1);
    acc[key] = value;
    return acc;
  }, {});

  return {
    playerPits: parsePitRow(parts.P),
    opponentPits: parsePitRow(parts.O),
    playerStore: Number.parseInt(parts.PS || "0", 10) || 0,
    opponentStore: Number.parseInt(parts.OS || "0", 10) || 0,
    turn: parts.T || "player",
    status: parts.ST || "in_progress",
    lastAction: parts.LA || "-",
    winner: parts.W || "-",
  };
};

const parseLastPit = (lastAction) => {
  if (!lastAction || lastAction === "-") {
    return null;
  }
  const base = lastAction.split(",")[0] || "";
  if (!base.startsWith("pit")) {
    return null;
  }
  const value = Number.parseInt(base.slice(3), 10);
  if (!Number.isFinite(value) || value < 1 || value > 6) {
    return null;
  }
  return value;
};

const buildBeadOffsets = (count, seed) => {
  const beads = [];
  const maxBeads = Math.min(36, Math.max(0, count));
  for (let index = 0; index < maxBeads; index += 1) {
    const a = (seed * 31 + index * 17) % 360;
    const r = 20 + ((seed * 19 + index * 11) % 24);
    const x = 50 + Math.cos((a * Math.PI) / 180) * (r * 0.75);
    const y = 50 + Math.sin((a * Math.PI) / 180) * (r * 0.75);
    beads.push({ x, y });
  }
  return beads;
};

const Pit = ({ label, count, active }) => {
  const beads = useMemo(() => buildBeadOffsets(count, Number(label)), [count, label]);
  return (
    <div className={`pit${active ? " pit--active" : ""}`} aria-label={`Pit ${label}: ${count} seeds`}>
      <div className="pit__beads" aria-hidden="true">
        {beads.map((bead, index) => (
          <span
            key={`${label}-${index}`}
            className="bead"
            style={{ left: `${bead.x}%`, top: `${bead.y}%` }}
          />
        ))}
      </div>
      <div className="pit__count">{count}</div>
      <div className="pit__label">{label}</div>
    </div>
  );
};

const Store = ({ title, count }) => {
  const beads = useMemo(() => buildBeadOffsets(count, count + 7), [count]);
  return (
    <div className="store" aria-label={`${title}: ${count} seeds`}>
      <div className="store__title">{title}</div>
      <div className="store__well">
        {beads.map((bead, index) => (
          <span
            key={`${title}-${index}`}
            className="bead bead--small"
            style={{ left: `${bead.x}%`, top: `${bead.y}%` }}
          />
        ))}
      </div>
      <div className="store__count">{count}</div>
    </div>
  );
};

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const snapshot = isSnapshotPayload(latestPayload) ? latestPayload : null;
  const parsedState = useMemo(() => parseState(snapshot?.state), [snapshot?.state]);
  const lastPit = parseLastPit(parsedState.lastAction);
  const error = snapshot?.legal === false ? snapshot?.error : null;

  return (
    <GameWidgetShell
      title="Mancala MCP"
      subtitle="Type a pit number 1-6 in chat. The board updates only from tool output."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="mancala_snapshot"
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
        "Player pits are 1-6 from left to right.",
        "Opponent pits are mirrored.",
      ]}
    >
      <section className="board" aria-label="Mancala board">
        <Store title="Opponent Store" count={parsedState.opponentStore} />
        <div className="board__middle">
          <div className="pit-row pit-row--opponent">
            {parsedState.opponentPits
              .slice()
              .reverse()
              .map((count, index) => {
                const label = PIT_LABELS[PIT_LABELS.length - 1 - index];
                return (
                  <Pit
                    key={`op-${label}`}
                    label={label}
                    count={count}
                    active={Number(label) === lastPit}
                  />
                );
              })}
          </div>
          <div className="pit-row pit-row--player">
            {parsedState.playerPits.map((count, index) => {
              const label = PIT_LABELS[index];
              return (
                <Pit
                  key={`pl-${label}`}
                  label={label}
                  count={count}
                  active={Number(label) === lastPit}
                />
              );
            })}
          </div>
        </div>
        <Store title="Player Store" count={parsedState.playerStore} />
      </section>
    </GameWidgetShell>
  );
}
