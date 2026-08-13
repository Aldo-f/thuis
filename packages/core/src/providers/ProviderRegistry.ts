import { ProviderAdapter } from "./ProviderAdapter.js";

/**
 * Singleton registry for all provider adapters.
 *
 * The registry is responsible for
 *   • registering adapters by name
 *   • looking up a single adapter
 *   • listing all adapters
 *   • disposing all adapters when the application shuts down
 */
export class ProviderRegistry {
  private static instance: ProviderRegistry;
  private providers = new Map<string, ProviderAdapter>();

  private constructor() {}

  /**
   * Retrieve the singleton instance.
   */
  static getInstance(): ProviderRegistry {
    if (!ProviderRegistry.instance) {
      ProviderRegistry.instance = new ProviderRegistry();
    }
    return ProviderRegistry.instance;
  }

  /**
   * Register an adapter. If an adapter with the same name already exists, the
   * registration will be ignored to keep the registry deterministic.
   */
  async register(adapter: ProviderAdapter): Promise<void> {
    const name = adapter.name;
    if (this.providers.has(name)) return;
    this.providers.set(name, adapter);
    if (typeof adapter.init === 'function') {
      await adapter.init();
    }
  }

  /**
   * Retrieve a provider by name.
   */
  get(name: string): ProviderAdapter | undefined {
    return this.providers.get(name);
  }

  /**
   * Retrieve all registered provider adapters.
   */
  getAll(): ProviderAdapter[] {
    return Array.from(this.providers.values());
  }

  /**
   * Dispose all providers and clear the registry.
   */
  async dispose(): Promise<void> {
    const promises = [];
    for (const provider of this.providers.values()) {
      promises.push(provider.dispose());
    }
    await Promise.all(promises);
    this.providers.clear();
  }
}
