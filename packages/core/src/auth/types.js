import { z } from "zod";
// ─── Credentials ────────────────────────────────────────────
export const VrtCredentialsSchema = z.object({
    email: z.string().email("Ongeldig e-mailadres"),
    password: z.string().min(1, "Wachtwoord is verplicht"),
});
// ─── Tokens ─────────────────────────────────────────────────
export const VrtTokensSchema = z.object({
    accessToken: z.string().min(1),
    videoToken: z.string().min(1),
    refreshToken: z.string().min(1),
    expiresAt: z.number(), // Unix timestamp (seconds) when accessToken expires
    acquiredAt: z.number(), // Unix timestamp (seconds) when tokens were acquired
});
// ─── Login response from /perform_login ─────────────────────
export const VrtLoginResponseSchema = z.object({
    redirectUrl: z.string().url().optional(),
    errorCode: z.union([z.number(), z.string()]).optional(),
    errorMessage: z.string().optional(),
});
// ─── Player token response ──────────────────────────────────
export const VrtPlayerTokenResponseSchema = z.object({
    vrtPlayerToken: z.string(),
});
export const TOKEN_KEYS = {
    ACCESS_TOKEN: "vrtnu-site_profile_at",
    VIDEO_TOKEN: "vrtnu-site_profile_vt",
    REFRESH_TOKEN: "vrtnu-site_profile_rt",
    TOKEN_META: "vrtnu_token_meta",
};
