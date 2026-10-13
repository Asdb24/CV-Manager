import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { environment } from "../../scripts/config.mjs";

const client = environment("desktop");
export default defineConfig({
  plugins: [react()],
  define: { __CLIENT_CONFIGURATION__: JSON.stringify(client) },
  server: {
    host: client.desktop_host,
    port: client.desktop_port,
    strictPort: true,
  },
  build: { outDir: "dist", emptyOutDir: true },
});
