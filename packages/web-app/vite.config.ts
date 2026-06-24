import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  plugins: [react(), tailwindcss()],
  base: "/",
  resolve: {
    alias: {
      "@thuis/core": path.resolve(__dirname, "../core/src"),
      "@thuis/ytdlp-service": path.resolve(__dirname, "../ytdlp-service/src"),
    },
  },
  build: {
    outDir: "dist",
    sourcemap: true,
  },
  server: {
    proxy: {
      "/vrtbe": {
        target: "https://www.vrt.be",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/vrtbe/, ""),
      },
      "/loginvrt": {
        target: "https://login.vrt.be",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/loginvrt/, ""),
      },
      "/api": {
        target: "http://localhost:3001",
        changeOrigin: true,
      },
    },
  },
});
