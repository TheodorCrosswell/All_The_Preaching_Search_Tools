import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/dist/",
  build: {
    outDir: "dist", // This is the default, but shown for clarity
    assetsDir: "assets", // This is also the default
  },
});
