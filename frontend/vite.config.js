import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    // The backend allows this address in its CORS settings (backend/.env.example)
    port: 5173,
  },
});
