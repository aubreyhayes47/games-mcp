import { useEffect } from "react";
import "./app.css";
import { useOpenAiGlobal } from "./hooks/useOpenAiGlobal";

const normalizeToolOutput = (toolOutput) => {
  if (!toolOutput) {
    return null;
  }
  if (toolOutput.structuredContent) {
    return toolOutput.structuredContent;
  }
  return toolOutput;
};

const isRollPayload = (payload) =>
  payload?.type === "rpg_dice_roll" && Array.isArray(payload?.rolls);

export default function App() {
  const toolOutput = useOpenAiGlobal("toolOutput");
  const latestPayload = normalizeToolOutput(toolOutput);
  const roll = isRollPayload(latestPayload) ? latestPayload : null;

  const isWaitingForTool = !isRollPayload(latestPayload) && latestPayload !== null;

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

  return (
    <main className="app">
      <header className="app__header">
        <div>
          <h1>RPG Dice MCP</h1>
          <p className="app__subtitle">
            Type a roll in chat (e.g., roll 2d6). The widget updates only from tool
            output.
          </p>
        </div>
      </header>

      <section className="status">
        <div>
          <strong>Sides:</strong> {roll?.sides || "-"}
        </div>
        <div>
          <strong>Count:</strong> {roll?.count || "-"}
        </div>
        <div>
          <strong>Total:</strong> {roll?.total ?? "-"}
        </div>
      </section>

      <section className="tray">
        {isWaitingForTool ? (
          <div className="tray__waiting" role="status">
            <p>Waiting for the next roll...</p>
          </div>
        ) : (
          <div className="tray__rolls">
            {roll?.rolls?.length ? (
              roll.rolls.map((value, index) => (
                <div key={`roll-${value}-${index}`} className="die">
                  <span>{value}</span>
                </div>
              ))
            ) : (
              <div className="die die--empty">-</div>
            )}
          </div>
        )}
      </section>

      <section className="tray-meta">
        <span>Supported dice: d4, d6, d8, d10, d12, d20, d100.</span>
        <p className="tray-note">One tool call can roll multiple dice of a type.</p>
      </section>
    </main>
  );
}
