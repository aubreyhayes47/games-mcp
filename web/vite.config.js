import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const widget = process.env.WIDGET || "chess";

export default defineConfig({
  root: `widgets/${widget}`,
  plugins: [react()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
    cssCodeSplit: false,
    rollupOptions: {
      output: {
        entryFileNames: "widget.js",
        assetFileNames: (assetInfo) => {
          if (assetInfo.name && assetInfo.name.endsWith(".css")) {
            return "widget.css";
          }
          return "assets/[name][extname]";
        },
        inlineDynamicImports: true
      }
    }
  }
});
