import {
  AuthenticationError,
  InvalidCredentialsError,
  VrtAuthService,
} from "@thuis/core";
import * as http from "node:http";

interface LoginBody {
  email?: string;
  password?: string;
}

function sendJson(
  res: http.ServerResponse,
  statusCode: number,
  data: unknown,
): void {
  const body = JSON.stringify(data);
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
  };
  res.writeHead(statusCode, headers);
  res.end(body);
}

function parseBody(req: http.IncomingMessage): Promise<string> {
  return new Promise<string>((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => {
      chunks.push(chunk);
    });
    req.on("end", () => {
      resolve(Buffer.concat(chunks).toString("utf-8"));
    });
    req.on("error", reject);
  });
}

function handleCors(res: http.ServerResponse): void {
  res.writeHead(204, {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
  });
  res.end();
}

export function createServer(): http.Server {
  const server = http.createServer(
    async (req: http.IncomingMessage, res: http.ServerResponse) => {
      // Handle CORS preflight
      if (req.method === "OPTIONS") {
        handleCors(res);
        return;
      }

      // Only accept POST /api/auth/vrt-login
      if (req.method !== "POST" || req.url !== "/api/auth/vrt-login") {
        res.writeHead(404);
        res.end();
        return;
      }

      try {
        // Parse JSON body
        let body: LoginBody;
        try {
          const raw = await parseBody(req);
          body = JSON.parse(raw) as LoginBody;
        } catch {
          sendJson(res, 400, { error: "Invalid JSON body" });
          return;
        }

        // Validate required fields
        if (!body.email || !body.password) {
          sendJson(res, 400, {
            error: "Email and password are required",
          });
          return;
        }

        // Perform the full OIDC login flow server-side
        const authService = new VrtAuthService({
          baseUrl: "https://www.vrt.be",
          loginUrl: "https://login.vrt.be",
        });

        const tokens = await authService.login({
          email: body.email,
          password: body.password,
        });

        sendJson(res, 200, tokens);
      } catch (err: unknown) {
        if (err instanceof InvalidCredentialsError) {
          sendJson(res, 401, { error: err.message });
        } else if (err instanceof AuthenticationError) {
          sendJson(res, 401, { error: err.message });
        } else {
          console.error("Unexpected error during login:", err);
          sendJson(res, 500, { error: "Interne serverfout" });
        }
      }
    },
  );

  return server;
}
