---
id: credential-vault
title: Credential Vault
sidebar_position: 4
---

# Credential Vault

The **Credential Vault** stores user credentials for each media provider securely. It abstracts away the underlying storage mechanism so the same API works in the web app, the Electron desktop app, and in tests.

## Architecture

- **Master password** – entered once on first launch. It is never persisted; it is used to derive an encryption key via PBKDF2.
- **Encryption** – credentials are encrypted with AES‑GCM using the derived key.
- **Storage**
  - **Web** – encrypted blob is saved in IndexedDB.
  - **Electron** – encrypted blob is saved in the OS keychain (via `keytar`).
- **Auto‑lock** – after a configurable period of inactivity (default 5 minutes) the vault clears the decryption key from memory and requires the master password again.

## API

```ts
/** Initialise the vault – prompts for the master password if needed. */
init(): Promise<void>;

/** Store credentials for a provider. */
saveCredentials(providerId: string, credentials: ProviderCredentials): Promise<void>;

/** Retrieve stored credentials. Returns `null` if none exist. */
getCredentials(providerId: string): Promise<ProviderCredentials | null>;

/** Delete credentials for a provider. */
removeCredentials(providerId: string): Promise<void>;

/** Change the master password – re‑encrypts all stored entries. */
changeMasterPassword(oldPwd: string, newPwd: string): Promise<void>;
```

## Usage Flow

1. **First launch** – the UI shows a *Vault Setup* screen. The user creates a master password.
2. The password is used to derive an encryption key and encrypt an empty credentials store.
3. When a provider adapter needs credentials, it calls `vault.getCredentials(providerId)`. If the vault is locked, the UI asks the user to enter the master password again.
4. After the user logs in to a provider, the adapter saves the token with `vault.saveCredentials(providerId, creds)`.
5. The vault automatically locks after the inactivity timeout; any subsequent call triggers a password prompt.

## Security Considerations

- The master password never leaves the client side; it is not sent to the backend.
- Encryption keys are kept only in memory while the vault is unlocked.
- In Electron, the encrypted blob is stored using the OS‑provided secure storage (Keychain on macOS, Credential Manager on Windows, Secret Service on Linux).
- In the browser, the encrypted blob lives in IndexedDB, which is isolated per origin.
- Auto‑lock minimizes exposure if the device is left unattended.

For a deeper dive, see the source code in `packages/core/src/vault/`.
