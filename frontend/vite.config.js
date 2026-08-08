import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Proxy encaminha as chamadas da API para o backend FastAPI em dev.
// ponytail: proxy em vez de CORS no backend; se for servir em domínios
// separados em produção, habilitar CORS lá.
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/convert": "http://localhost:8000",
      "/health": "http://localhost:8000",
    },
  },
  test: { environment: "node" },
});
