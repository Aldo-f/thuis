// CredentialVault implementation for web and Electron
// Stores encrypted credentials in IndexedDB (or Electron safeStorage) and keeps decrypted data only in memory.
// All errors are presented in Dutch as required.

export type ProviderCredential = {
  provider: string;
  email: string;
  password: string; // decrypted, never persisted directly
};

export class VaultLockedError extends Error {
  constructor() {
    super("Ongeldig hoofdwachtwoord");
    this.name = "VaultLockedError";
  }
}

export class MissingPasswordError extends Error {
  constructor() {
    super("Wachtwoord vereist");
    this.name = "MissingPasswordError";
  }
}

interface EncryptedBlob {
  // salt(16) | iv(12) | ciphertext (ArrayBuffer)
  data: Uint8Array; // concatenated bytes
}

interface VaultConfig {
  /** Auto‑lock timeout in milliseconds. Default 5 minutes. */
  autoLockMs?: number;
}

/** Simple IndexedDB wrapper – stores a single Uint8Array under key "blob" */
class IndexedDBStore {
  private inMemory = new Map<string, Uint8Array>();
  
  private useSafeStorage = typeof window !== 'undefined' &&
    (window as { thuisAPI?: { vault?: { encrypt?: (data: string) => Promise<string>; decrypt?: (data: string) => Promise<string> } } }).thuisAPI?.vault?.encrypt && 
    (window as { thuisAPI?: { vault?: { encrypt?: (data: string) => Promise<string>; decrypt?: (data: string) => Promise<string> } } }).thuisAPI?.vault?.decrypt;

  private dbName = "credential-vault";
  private storeName = "blobStore";

  private async getDB(): Promise<IDBDatabase | { transaction: (storeName: string, mode: IDBTransactionMode) => IDBTransaction; close: () => void }> {
    if (typeof indexedDB === 'undefined') {
      // Mock for environments without IndexedDB (e.g., Node.js)
      const mockTx: IDBTransaction = {
        objectStore: (storeName: string) => ({
          put: (value: Uint8Array, key: string) => {
            this.inMemory.set(key, value);
            const req = {} as IDBRequest;
            setTimeout(() => {
              if (req.onsuccess) req.onsuccess({} as Event);
            }, 0);
            return req;
          },
          get: (key: string) => {
            const req = { result: this.inMemory.get(key) ?? null } as IDBRequest;
            setTimeout(() => {
              if (req.onsuccess) req.onsuccess({} as Event);
            }, 0);
            return req;
          },
          delete: (key: string) => {
            this.inMemory.delete(key);
            const req = {} as IDBRequest;
            setTimeout(() => {
              if (req.onsuccess) req.onsuccess({} as Event);
            }, 0);
            return req;
          },
        }),
        oncomplete: null,
        onerror: null,
      } as IDBTransaction;
      
      return {
        transaction: (storeName: string, mode: IDBTransactionMode) => mockTx,
        close: () => {},
      };
    }
    // Use real IndexedDB (or fake-indexeddb) when available
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, 1);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(this.storeName)) {
          db.createObjectStore(this.storeName);
        }
      };
      request.onsuccess = () => {
        resolve(request.result);
      };
      request.onerror = () => {
        reject(request.error);
      };
    });
  }

  public async set(blob: Uint8Array): Promise<void> {
    if (typeof indexedDB === 'undefined') {
      this.inMemory.set('blob', blob);
      return;
    }
    if (this.useSafeStorage) {
      const base64 = Buffer.from(blob).toString('base64');
      // @ts-expect-error - thuisAPI is injected by the Electron preload script
      await (window as { thuisAPI: { vault: { encrypt: (data: string) => Promise<string> } } }).thuisAPI.vault.encrypt(base64);
      // Store the encrypted base64 string in IndexedDB for retrieval later
      const db = await this.getDB();
      return new Promise((resolve, reject) => {
        const tx = db.transaction(this.storeName, "readwrite");
        const store = tx.objectStore(this.storeName);
        store.put(base64, "blob");
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
      });
    }
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);
      store.put(blob, "blob");
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }

  async get(): Promise<Uint8Array | null> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readonly");
      const store = tx.objectStore(this.storeName);
      const request = store.get("blob");
      request.onsuccess = async () => {
        const result = request.result as string | Uint8Array | undefined;
        if (result == null) {
          resolve(null);
          return;
        }
        if (this.useSafeStorage && typeof result === 'string') {
          // Decrypt via bridge
          // @ts-expect-error - thuisAPI is injected by the Electron preload script
          const decryptedBase64 = await (window as { thuisAPI: { vault: { decrypt: (data: string) => Promise<string> } } }).thuisAPI.vault.decrypt(result);
          const bytes = Buffer.from(decryptedBase64, 'base64');
          resolve(new Uint8Array(bytes));
        } else if (result instanceof Uint8Array) {
          resolve(result);
        } else {
          // Assume raw Uint8Array stored as is
          resolve(new Uint8Array(result as unknown as Uint8Array));
        }
      };
      request.onerror = () => reject(request.error);
    });
  }

  async clear(): Promise<void> {
    const db = await this.getDB();
    return new Promise((resolve, reject) => {
      const tx = db.transaction(this.storeName, "readwrite");
      const store = tx.objectStore(this.storeName);
      store.delete("blob");
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
    });
  }
}

/** Crypto helper using Web Crypto API */
class CryptoHelper {
  private static readonly iterations = 600_000; // per spec
  private static readonly hash = "SHA-256";
  private static readonly keyLen = 256; // bits

  static async deriveKey(password: string, salt: BufferSource): Promise<CryptoKey> {
    const enc = new TextEncoder();
    const keyMaterial = await crypto.subtle.importKey(
      "raw",
      enc.encode(password),
      { name: "PBKDF2" },
      false,
      ["deriveKey"]
    );
    return crypto.subtle.deriveKey(
{
        name: "PBKDF2",
        salt: salt as BufferSource,
        iterations: this.iterations,
        hash: this.hash,
      },
      keyMaterial,
      { name: "AES-GCM", length: this.keyLen },
      false,
      ["encrypt", "decrypt"]
    );
  }

  static async encrypt(plain: string, password: string): Promise<Uint8Array> {
    const enc = new TextEncoder();
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const key = await this.deriveKey(password, salt);
    const ct = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, enc.encode(plain));
    // concatenate salt+iv+ciphertext
    const ctArray = new Uint8Array(ct);
    const result = new Uint8Array(salt.length + iv.length + ctArray.length);
    result.set(salt, 0);
    result.set(iv, salt.length);
    result.set(ctArray, salt.length + iv.length);
    return result;
  }

  static async decrypt(data: Uint8Array, password: string): Promise<string> {
    const salt = data.slice(0, 16);
    const iv = data.slice(16, 28);
    const ct = data.slice(28);
    const key = await this.deriveKey(password, salt);
    const plainBuf = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, ct);
    const dec = new TextDecoder();
    return dec.decode(plainBuf);
  }
}

/** Main service */
export class CredentialVault {
  private config: Required<VaultConfig> = { autoLockMs: 5 * 60 * 1000 };
  private locked = true;
  private masterPassword: string | null = null;
  private cache: Map<string, ProviderCredential> = new Map();
  private autoLockTimer: ReturnType<typeof setTimeout> | null = null;
  private store = new IndexedDBStore();

  constructor(config?: VaultConfig) {
    if (config?.autoLockMs) this.config.autoLockMs = config.autoLockMs;
  }

  /** Reset auto‑lock timer */
  private resetTimer() {
    if (this.autoLockTimer) clearTimeout(this.autoLockTimer);
    this.autoLockTimer = setTimeout(() => this.lock(), this.config.autoLockMs);
  }

  /** Is the vault currently locked? */
  isLocked(): boolean {
    return this.locked;
  }

  /** Lock the vault – purge decrypted data */
  lock(): void {
    this.locked = true;
    this.masterPassword = null;
    this.cache.clear();
    if (this.autoLockTimer) clearTimeout(this.autoLockTimer);
    this.autoLockTimer = null;
  }

  /** Unlock using master password; throws VaultLockedError on failure */
  async unlock(masterPassword: string): Promise<void> {
    if (!masterPassword) throw new MissingPasswordError();
    const blob = await this.store.get();
    if (!blob) {
      // first‑time setup – create empty encrypted blob
      const empty = await CryptoHelper.encrypt(JSON.stringify([]), masterPassword);
      await this.store.set(empty);
      this.masterPassword = masterPassword;
      this.locked = false;
      this.cache.clear();
      this.resetTimer();
      return;
    }
    try {
      const plain = await CryptoHelper.decrypt(blob, masterPassword);
      const arr: ProviderCredential[] = JSON.parse(plain);
      this.cache.clear();
      for (const cred of arr) this.cache.set(cred.provider, cred);
      this.masterPassword = masterPassword;
      this.locked = false;
      this.resetTimer();
    } catch (e) {
      // decryption failure → wrong password
      throw new VaultLockedError();
    }
  }

  /** Persist current cache to storage */
  private async persist(): Promise<void> {
    if (!this.masterPassword) throw new VaultLockedError();
    const arr = Array.from(this.cache.values());
    const plain = JSON.stringify(arr);
    const encrypted = await CryptoHelper.encrypt(plain, this.masterPassword);
    await this.store.set(encrypted);
  }

  private ensureUnlocked() {
    if (this.locked) throw new VaultLockedError();
    this.resetTimer();
  }

  /** Add or replace credentials for a provider */
  async addCredentials(provider: string, email: string, password: string): Promise<void> {
    this.ensureUnlocked();
    this.cache.set(provider, { provider, email, password });
    await this.persist();
  }

  /** Retrieve credentials for a provider – throws if not found */
  getCredentials(provider: string): ProviderCredential | null {
    this.ensureUnlocked();
    return this.cache.get(provider) ?? null;
  }

  /** Remove credentials for a provider */
  async removeCredentials(provider: string): Promise<void> {
    this.ensureUnlocked();
    this.cache.delete(provider);
    await this.persist();
  }

  /** List providers (email only, never password) */
  listProviders(): { provider: string; email: string }[] {
    this.ensureUnlocked();
    return Array.from(this.cache.values()).map((c) => ({ provider: c.provider, email: c.email }));
  }
}
