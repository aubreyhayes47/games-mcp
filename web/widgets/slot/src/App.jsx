import { useEffect } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";
import { SYMBOL_LABELS } from "./icons.js";

const normalizeToolOutput = (toolOutput) => {
  if (!toolOutput) {
    return null;
  }
  if (toolOutput.structuredContent) {
    return toolOutput.structuredContent;
  }
  return toolOutput;
};

const isSlotPayload = (payload) =>
  payload?.type === "slot_snapshot" && typeof payload?.state === "string";

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const snapshot = isSlotPayload(latestPayload) ? latestPayload : null;

  const isWaitingForTool = !isSlotPayload(latestPayload) && latestPayload !== null;

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

  const reels = snapshot?.reels?.length ? snapshot.reels : ["-", "-", "-"];
  const payout = snapshot?.payout ?? 0;

  return (
    <main className="app">
      <header className="app__header">
        <div>
          <h1>Slot Machine MCP</h1>
          <p className="app__subtitle">
            Type "spin" in chat. The reels update only from tool output.
          </p>
        </div>
      </header>

      <section className="status">
        <div>
          <strong>Stack:</strong> {snapshot?.stack ?? "-"}
        </div>
        <div>
          <strong>Bet:</strong> {snapshot?.bet ?? "-"}
        </div>
        <div>
          <strong>Payout:</strong> {payout}
        </div>
      </section>

      <section className="reel-area">
        {isWaitingForTool ? (
          <div className="reel-area__waiting" role="status">
            <p>Waiting for the next spin...</p>
          </div>
        ) : (
          <div className="reels">
            {reels.map((symbol, index) => (
              <div key={`reel-${symbol}-${index}`} className="reel">
                <span>{SYMBOL_LABELS[symbol] || symbol}</span>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="reel-meta">
        <span>Classic table with weighted symbols.</span>
        <p className="reel-note">
          Matching all three symbols pays out a multiplier on your bet.
        </p>
      </section>
    </main>
  );
}
