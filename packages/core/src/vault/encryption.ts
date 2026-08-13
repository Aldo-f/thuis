// Get a reference to the crypto.subtle API
let subtle: SubtleCrypto;
if (typeof window !== 'undefined' && window.crypto && window.crypto.subtle) {
  subtle = window.crypto.subtle;
} else if (typeof global !== 'undefined' && global.crypto && global.crypto.subtle) {
  subtle = global.crypto.subtle;
} else {
  // Try to get from Node.js crypto webcrypto
  const { webcrypto } = await import('crypto');
  subtle = webcrypto.subtle as unknown as SubtleCrypto;
}

// Function to get cryptographically strong random values
async function getRandomValues(array: Uint8Array): Promise<Uint8Array> {
  if (typeof window !== 'undefined' && window.crypto) {
    window.crypto.getRandomValues(array);
    return array;
  } else {
    // Node.js
    const { randomBytes } = await import('crypto');
    const bytes = randomBytes(array.length);
    array.set(bytes);
    return array;
  }
}

// Detect if we are in Electron renderer process
const isElectron = typeof window !== 'undefined' && 
  typeof (window as { process?: { type?: string } }).process?.type === 'string' && 
  (window as { process?: { type?: string } }).process?.type === 'renderer';

// For Electron, we need to access safeStorage via the electron module
let safeStorage: { encryptString: (data: string) => string; decryptString: (data: string) => string } | null = null;
if (isElectron) {
  try {
    // In renderer, we might need to use require if nodeIntegration is enabled
    // or via contextBridge. We'll assume we can require 'electron'
    // eslint-disable-next-line @typescript-eslint/no-require-imports
    const { safeStorage: ss } = require('electron');
    safeStorage = ss;
  } catch {
    // If we cannot require electron, fall back to false
    console.warn('Could not load electron safeStorage');
  }
}

/**
 * Derive a cryptographic key from a password and salt using PBKDF2-SHA256
 * @param password - The password to derive key from
 * @param salt - The salt to use for derivation (16 bytes expected)
 * @returns A CryptoKey for AES-GCM
 */
export async function deriveKey(password: string, salt: Uint8Array): Promise<CryptoKey> {
  // Import the password as a raw key
  const passwordKey = await subtle.importKey(
    'raw',
    new TextEncoder().encode(password),
    { name: 'PBKDF2' },
    false,
    ['deriveKey']
  );

  // Derive a 256-bit key for AES-GCM
  return await subtle.deriveKey(
    {
      name: 'PBKDF2',
      // Cast to BufferSource to satisfy TypeScript
      salt: salt as BufferSource,
      iterations: 600000,
      hash: 'SHA-256'
    },
    passwordKey,
    { name: 'AES-GCM', length: 256 },
    false,
    ['encrypt', 'decrypt']
  );
}

/**
 * Encrypt plaintext using AES-GCM with a randomly generated IV.
 * In Electron, uses safeStorage.encryptString as an alternative (ignores the key).
 * @param key - The encryption key (ignored in Electron)
 * @param plaintext - The text to encrypt
 * @returns Promise resolving to encrypted data (salt+iv+ciphertext as Uint8Array in web, or safeStorage encrypted string in Electron)
 */
export async function encrypt(key: CryptoKey, plaintext: string): Promise<Uint8Array | string> {
  if (isElectron && safeStorage) {
    // In Electron, use safeStorage to encrypt the plaintext directly
    // Note: safeStorage.encryptString is synchronous, but we wrap in Promise to maintain async interface
    const encrypted = safeStorage.encryptString(plaintext);
    // We return a string (the encrypted string from safeStorage)
    return encrypted;
  } else {
    // Web crypto implementation
    // Generate a random salt (16 bytes)
    const salt = await getRandomValues(new Uint8Array(16));
    // Generate a random IV (12 bytes for AES-GCM)
    const iv = await getRandomValues(new Uint8Array(12));
    // Encode the plaintext to bytes
    const encoder = new TextEncoder();
    const data = encoder.encode(plaintext);
    
    // Encrypt the data
    const ciphertextBuffer = await subtle.encrypt(
      { name: 'AES-GCM', iv: iv as BufferSource },
      key,
      data
    );
    const ciphertext = new Uint8Array(ciphertextBuffer);
    
    // Combine salt + iv + ciphertext
    const result = new Uint8Array(salt.length + iv.length + ciphertext.length);
    result.set(salt, 0);
    result.set(iv, salt.length);
    result.set(ciphertext, salt.length + iv.length);
    
    return result;
  }
}

/**
 * Decrypt ciphertext using AES-GCM.
 * In Electron, uses safeStorage.decryptString as an alternative (ignores the key).
 * @param key - The decryption key (ignored in Electron)
 * @param ciphertext - The encrypted data (Uint8Array in web, string in Electron)
 * @returns Promise resolving to the decrypted plaintext string
 */
export async function decrypt(key: CryptoKey, ciphertext: Uint8Array | string): Promise<string> {
  if (isElectron && safeStorage && typeof ciphertext === 'string') {
    // In Electron, use safeStorage to decrypt the string directly
    const decrypted = safeStorage.decryptString(ciphertext);
    return decrypted;
  } else {
    // Web crypto implementation
    if (ciphertext instanceof Uint8Array) {
      // Extract salt (first 16 bytes), iv (next 12 bytes), and ciphertext (rest)
      const salt = ciphertext.slice(0, 16);
      const iv = ciphertext.slice(16, 28);
      const ciphertextBytes = ciphertext.slice(28);
      
      // Decrypt
      const plaintextBuffer = await subtle.decrypt(
{ name: 'AES-GCM', iv: iv as BufferSource },
        key,
        ciphertextBytes
      );
      const decoder = new TextDecoder();
      return decoder.decode(plaintextBuffer);
    } else {
      throw new Error('Invalid ciphertext format for web decryption');
    }
  }
}