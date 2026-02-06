export function normalizeToolOutput(toolOutput) {
  if (!toolOutput) {
    return null;
  }
  if (toolOutput.structuredContent) {
    return toolOutput.structuredContent;
  }
  return toolOutput;
}
