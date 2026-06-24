import { createServer } from "./server.js";

const PORT = Number.parseInt(process.env.AUTH_PORT ?? "3001", 10);

const server = createServer();

server.listen(PORT, () => {
  console.log(`Auth server listening on port ${PORT}`);
});

function shutdown(): void {
  console.log("Shutting down auth server...");
  server.close(() => {
    console.log("Auth server closed");
    process.exit(0);
  });
  // Force exit if graceful shutdown takes too long
  setTimeout(() => process.exit(1), 5000).unref();
}

process.on("SIGTERM", shutdown);
process.on("SIGINT", shutdown);
