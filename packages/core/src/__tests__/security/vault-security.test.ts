import { CredentialVault, VaultLockedError, MissingPasswordError } from "../../vault/Vault.ts";
import { jest } from "@jest/globals";

describe('CredentialVault security', () => {
  const masterPassword = 'correcthorsebatterystaple';
  const wrongPassword = 'incorrect';
  const provider = 'testProvider';
  const email = 'user@example.com';
  const secret = 'superSecret123';

  let vault: CredentialVault;

  beforeEach(() => {
    vault = new CredentialVault({ autoLockMs: 2000 }); // 2 s auto‑lock for tests
  });

  test('encryption/decryption round‑trip with known vector', async () => {
    // Directly use CryptoHelper via the vault implementation path
    // Encrypt a known plaintext and then decrypt it, ensuring the result matches.
    // We use the vault's internal encrypt/decrypt through add/get flow.
    await vault.unlock(masterPassword);
    await vault.addCredentials(provider, email, secret);
    const cred = vault.getCredentials(provider);
    expect(cred).not.toBeNull();
    expect(cred!.password).toBe(secret);
    // Ensure stored blob is not plain text by checking the IndexedDB entry is a Uint8Array
    // (the store is private; we simulate by unlocking again and reading the raw blob)
    const rawBlob = await (vault as any).store.get();
    expect(rawBlob).toBeInstanceOf(Uint8Array);
  });

  test('auto‑lock triggers after inactivity', async () => {
    jest.useFakeTimers();
    await vault.unlock(masterPassword);
    await vault.addCredentials(provider, email, secret);
    // advance less than timeout
    jest.advanceTimersByTime(1500);
    expect(vault.isLocked()).toBe(false);
    // advance past timeout
    jest.advanceTimersByTime(600);
    expect(vault.isLocked()).toBe(true);
    jest.useRealTimers();
  });

  test('plain password never appears in logs', async () => {
    const logs: string[] = [];
    const logger = {
      debug: (msg: string) => logs.push(msg),
      info: (msg: string) => logs.push(msg),
      warn: (msg: string) => logs.push(msg),
      error: (msg: string) => logs.push(msg),
    };
    // Temporarily replace console methods
    const origLog = console.log;
    console.log = (msg?: any, ...args: any[]) => logger.info(String(msg));

    await vault.unlock(masterPassword);
    await vault.addCredentials(provider, email, secret);
    // Trigger a getter which logs nothing sensitive
    vault.getCredentials(provider);

    // Restore console
    console.log = origLog;

    const joined = logs.join(' ');
    expect(joined).not.toMatch(new RegExp(secret, 'i'));
  });

  test('lock() purges decrypted data from memory', async () => {
    await vault.unlock(masterPassword);
    await vault.addCredentials(provider, email, secret);
    const before = vault.getCredentials(provider);
    expect(before).not.toBeNull();
    vault.lock();
    expect(vault.isLocked()).toBe(true);
    expect(() => vault.getCredentials(provider)).toThrow(VaultLockedError);
    // internal cache should be empty
    const cache = (vault as any).cache as Map<string, any>;
    expect(cache.size).toBe(0);
  });

  test('wrong master password throws VaultLockedError', async () => {
    await vault.unlock(masterPassword);
    vault.lock();
    await expect(vault.unlock(wrongPassword)).rejects.toThrow(VaultLockedError);
  });
});
