import { CredentialVault, VaultLockedError, MissingPasswordError } from "../../vault/Vault.ts";
import { jest } from "@jest/globals";

describe('CredentialVault', () => {
  const password = 'correcthorsebatterystaple';
  let vault: CredentialVault;

  beforeEach(() => {
    vault = new CredentialVault({ autoLockMs: 2000 }); // 2s for faster test
  });

  test('unlock creates empty vault when none exists', async () => {
    await vault.unlock(password);
    expect(vault.isLocked()).toBe(false);
    expect(vault.listProviders()).toEqual([]);
  });

  test('add and get credentials', async () => {
    await vault.unlock(password);
    await vault.addCredentials('vrt', 'user@example.com', 'secret123');
    const cred = vault.getCredentials('vrt');
    expect(cred).toEqual({ provider: 'vrt', email: 'user@example.com', password: 'secret123' });
    expect(vault.listProviders()).toEqual([{ provider: 'vrt', email: 'user@example.com' }]);
  });

  test('remove credentials', async () => {
    await vault.unlock(password);
    await vault.addCredentials('vrt', 'u@e.com', 'p');
    await vault.removeCredentials('vrt');
    expect(vault.getCredentials('vrt')).toBeNull();
    expect(vault.listProviders()).toEqual([]);
  });

  test('lock clears memory', async () => {
    await vault.unlock(password);
    await vault.addCredentials('vrt', 'u@e.com', 'p');
    vault.lock();
    expect(vault.isLocked()).toBe(true);
    expect(() => vault.getCredentials('vrt')).toThrow(VaultLockedError);
  });

  test('wrong password throws', async () => {
    await vault.unlock(password);
    vault.lock();
    await expect(vault.unlock('wrong')).rejects.toThrow(VaultLockedError);
  });

  test('auto‑lock after inactivity', async () => {
    jest.useFakeTimers();
    await vault.unlock(password);
    await vault.addCredentials('a', 'e', 'p');
    // advance time less than timeout
    jest.advanceTimersByTime(1500);
    expect(vault.isLocked()).toBe(false);
    // advance beyond timeout
    jest.advanceTimersByTime(600);
    expect(vault.isLocked()).toBe(true);
    jest.useRealTimers();
  });
});
