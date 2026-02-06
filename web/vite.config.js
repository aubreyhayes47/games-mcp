import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";

const widget = process.env.WIDGET || "chess";

const buildConfig = (root) =>
  defineConfig({
    root,
    plugins: [react()],
    resolve: {
      alias: {
        "@shared": path.resolve(__dirname, "widgets/shared"),
      },
    },
    server: {
      fs: {
        allow: [path.resolve(__dirname)],
      },
    },
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

export default buildConfig(`widgets/${widget}`);
