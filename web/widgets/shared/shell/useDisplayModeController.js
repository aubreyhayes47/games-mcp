import { useEffect, useRef } from "react";

const MODE_INLINE = "inline";
const MODE_PIP = "pip";

async function requestMode(mode) {
  if (typeof window === "undefined" || !window.openai) {
    return;
  }
  const openai = window.openai;

  if (typeof openai.requestDisplayMode === "function") {
    try {
      await openai.requestDisplayMode(mode);
      return;
    } catch {
      try {
        await openai.requestDisplayMode({ mode });
        return;
      } catch {
        // Try fallback APIs below.
      }
    }
  }

  if (typeof openai.setDisplayMode === "function") {
    try {
      await openai.setDisplayMode(mode);
      return;
    } catch {
      try {
        await openai.setDisplayMode({ mode });
        return;
      } catch {
        // Try fallback APIs below.
      }
    }
  }

  if (typeof openai.displayMode === "function") {
    try {
      await openai.displayMode(mode);
    } catch {
      // Ignore unsupported method errors.
    }
  }
}

export function useDisplayModeController({
  isSessionGame,
  status,
  gameKey,
  autoPolicy = "auto_on_in_progress",
}) {
  const lastRequestedModeRef = useRef(null);
  const lastGameKeyRef = useRef(null);

  useEffect(() => {
    if (!isSessionGame || autoPolicy !== "auto_on_in_progress") {
      return;
    }

    if (lastGameKeyRef.current !== gameKey) {
      lastGameKeyRef.current = gameKey;
      lastRequestedModeRef.current = null;
    }

    const targetMode = status === "in_progress" ? MODE_PIP : MODE_INLINE;
    if (lastRequestedModeRef.current === targetMode) {
      return;
    }

    let cancelled = false;
    const run = async () => {
      await requestMode(targetMode);
      if (!cancelled) {
        lastRequestedModeRef.current = targetMode;
      }
    };

    run();

    return () => {
      cancelled = true;
    };
  }, [autoPolicy, gameKey, isSessionGame, status]);
}
