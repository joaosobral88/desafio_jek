import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  testMatch: "*.spec.js",
  workers: 1,
  use: { baseURL: "http://127.0.0.1:5173", headless: true },
  webServer: [
    {
      command: "..\\backend\\venv\\Scripts\\python.exe tests/backend_server.py",
      url: "http://127.0.0.1:8001/api/public/polls/",
      timeout: 30000,
    },
    {
      command: "npm.cmd run dev",
      url: "http://127.0.0.1:5173",
      env: { VITE_API_URL: "http://127.0.0.1:8001/api" },
    },
  ],
});
