import { ProviderRegistry } from './providers/ProviderRegistry.js';
import { VrtProviderAdapter } from './providers/vrt/VrtProviderAdapter.js';
import { VtmgoProviderAdapter } from './providers/vtmgo/VtmgoProviderAdapter.js';
import { PlaytvProviderAdapter } from './providers/playtv/PlaytvProviderAdapter.js';

/**
 * Initialize all provider adapters and register them with the singleton
 * ProviderRegistry. Should be called once at application startup.
 *
 * Returns the initialized registry instance.
 */
export async function initializeProviders(): Promise<ProviderRegistry> {
  const registry = ProviderRegistry.getInstance();

  // Detect if we're running in a browser environment
  const isBrowser = typeof window !== 'undefined' && typeof window.document !== 'undefined';
  
  // For VRT adapter, use API mode in browser (to proxy through auth server)
  // and direct mode in Node.js (for tests and server-side rendering)
  const vrtAdapterOptions = isBrowser 
    ? { loginMode: 'api' } as const 
    : { loginMode: 'direct' } as const;

  await registry.register(new VrtProviderAdapter(vrtAdapterOptions));
  await registry.register(new VtmgoProviderAdapter());
  await registry.register(new PlaytvProviderAdapter());

  return registry;
}
