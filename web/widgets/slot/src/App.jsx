import "./app.css";
import { SYMBOL_LABELS } from "./icons.js";
import { GameWidgetShell } from "@shared/shell/GameWidgetShell";
import { normalizeToolOutput } from "@shared/shell/normalizeToolOutput";
import { useOpenAiGlobal } from "@shared/shell/useOpenAiGlobal";

const isSlotPayload = (payload) =>
  payload?.type === "slot_snapshot" && typeof payload?.state === "string";

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const snapshot = isSlotPayload(latestPayload) ? latestPayload : null;

  const reels = snapshot?.reels?.length ? snapshot.reels : ["-", "-", "-"];
  const payout = snapshot?.payout ?? 0;
  const error = snapshot?.legal === false ? snapshot?.error : null;

  return (
    <GameWidgetShell
      title="Slot Machine MCP"
      subtitle="Type spin in chat. The reels update only from tool output."
      latestPayload={latestPayload}
      snapshot={snapshot}
      snapshotType="slot_snapshot"
      isSessionGame={true}
      status={snapshot?.status}
      turn={null}
      gameId={snapshot?.gameId || snapshot?.state}
      error={error}
      waitingMessage="Waiting for the next spin..."
      statusItems={[
        { label: "Stack", value: snapshot?.stack ?? "-" },
        { label: "Bet", value: snapshot?.bet ?? "-" },
        { label: "Payout", value: payout },
      ]}
      instructions={[
        "Matching all three symbols pays a multiplier.",
      ]}
    >
      <section className="reel-area">
        <div className="reels">
          {reels.map((symbol, index) => (
            <div key={`reel-${symbol}-${index}`} className="reel">
              <span>{SYMBOL_LABELS[symbol] || symbol}</span>
            </div>
          ))}
        </div>
      </section>
    </GameWidgetShell>
  );
}
