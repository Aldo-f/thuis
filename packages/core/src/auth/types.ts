import { z } from "zod";

// ─── Credentials ────────────────────────────────────────────

export const VrtCredentialsSchema = z.object({
  email: z.string().email("Ongeldig e-mailadres"),
  password: z.string().min(1, "Wachtwoord is verplicht"),
});

export type VrtCredentials = z.infer<typeof VrtCredentialsSchema>;

// ─── Tokens ─────────────────────────────────────────────────

export const VrtTokensSchema = z.object({
  accessToken: z.string().min(1),
  videoToken: z.string().min(1),
  refreshToken: z.string().min(1),
  expiresAt: z.number(),       // Unix timestamp (seconds) when accessToken expires
  acquiredAt: z.number(),       // Unix timestamp (seconds) when tokens were acquired
});

export type VrtTokens = z.infer<typeof VrtTokensSchema>;

// ─── Login response from /perform_login ─────────────────────

export const VrtLoginResponseSchema = z.object({
  redirectUrl: z.string().url().optional(),
  errorCode: z.union([z.number(), z.string()]).optional(),
  errorMessage: z.string().optional(),
});

export type VrtLoginResponse = z.infer<typeof VrtLoginResponseSchema>;

// ─── Player token response ──────────────────────────────────

export const VrtPlayerTokenResponseSchema = z.object({
  vrtPlayerToken: z.string(),
});

export type VrtPlayerTokenResponse = z.infer<typeof VrtPlayerTokenResponseSchema>;

// ─── Storage interface (pluggable backend) ──────────────────

export interface TokenStorage {
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  delete(key: string): Promise<void>;
}

export const TOKEN_KEYS = {
  ACCESS_TOKEN: "vrtnu-site_profile_at",
  VIDEO_TOKEN: "vrtnu-site_profile_vt",
  REFRESH_TOKEN: "vrtnu-site_profile_rt",
  TOKEN_META: "vrtnu_token_meta",
} as const;
