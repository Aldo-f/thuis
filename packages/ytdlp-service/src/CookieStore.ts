import { z } from "zod";
import { CredentialVault } from "@thuis/core";

// Netscape cookie file format (simplified) – each line: domain\t\t\t\t[options...]\n
const NetscapeCookieSchema = z.string().refine((val) => {
  // Basic check: at least 7 tab‑separated fields per line
  const lines = val.split("\n").filter(l => l && !l.startsWith("#"));
  return lines.every(line => line.split("\t").length >= 7);
}, { message: "Invalid Netscape cookie format" });

/**
 * Simple wrapper around {@link CredentialVault} to store yt‑dlp cookies.
 * Cookies are stored under a dedicated key "yt-dlp-cookies".
 * The vault must be unlocked before use – callers are responsible for that.
 */
export class CookieStore {
  private static readonly KEY = "yt-dlp-cookies";
  private vault: CredentialVault;

  constructor(vault: CredentialVault) {
    this.vault = vault;
  }

  /** Validate and encrypt cookie string */
  async saveCookies(cookies: string): Promise<void> {
    try {
      NetscapeCookieSchema.parse(cookies);
    } catch (e) {
      throw new Error(`Cookie validation failed: ${(e as Error).message}`);
    }
    // Store as a provider credential with dummy provider name
    const cred = {
      provider: CookieStore.KEY,
      email: "cookies",
      password: cookies, // encrypted by vault
    };
    // Ensure vault is unlocked – CredentialVault throws if locked
    // Use internal method addCredentials which persists via encrypt/decrypt
    await this.vault.addCredentials(cred.provider, cred.email, cred.password);
  }

  /** Decrypt and return stored cookies */
  async loadCookies(): Promise<string> {
    const cred = (this.vault as any).getCredentials(CookieStore.KEY);
    if (!cred) {
      throw new Error("No stored cookies found");
    }
    return cred.password;
  }

  /** Remove stored cookies */
  async clearCookies(): Promise<void> {
    await (this.vault as any).removeCredentials(CookieStore.KEY);
  }

  /** Simple validity check – returns true if a cookie entry exists.
   * For a deeper validation one could call yt‑dlp with the cookie file, but
   * that would require network I/O and is outside the scope of this class.
   */
  async ensureValidSession(): Promise<boolean> {
    const cred = (this.vault as any).getCredentials(CookieStore.KEY);
    return cred !== null;
  }
}
