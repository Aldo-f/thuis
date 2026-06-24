// Tests for stub adapters ensuring they throw ProviderNotSupportedError and are registered

import { ProviderRegistry } from '../../providers/ProviderRegistry.js';
import { VtmgoProviderAdapter, ProviderNotSupportedError as VtmgoError } from '../../providers/vtmgo/VtmgoProviderAdapter.js';
import { PlaytvProviderAdapter, ProviderNotSupportedError as PlaytvError } from '../../providers/playtv/PlaytvProviderAdapter.js';

// Helper to assert all adapter methods throw the expected error
async function expectAllMethodsThrow(adapter: any, ExpectedError: any, message: string) {
  await expect(adapter.login({})).rejects.toThrowError(new ExpectedError(message));
  await expect(adapter.search('')).rejects.toThrowError(new ExpectedError(message));
  await expect(adapter.getEpisode('')).rejects.toThrowError(new ExpectedError(message));
  await expect(adapter.resolveStream({} as any)).rejects.toThrowError(new ExpectedError(message));
}

describe('VtmgoProviderAdapter (stub)', () => {
  const adapter = new VtmgoProviderAdapter();
  const message = 'VTM GO wordt nog niet ondersteund';
  test('throws ProviderNotSupportedError on all methods', async () => {
    await expectAllMethodsThrow(adapter, VtmgoError, message);
  });
});

describe('PlaytvProviderAdapter (stub)', () => {
  const adapter = new PlaytvProviderAdapter();
  const message = 'Play.TV wordt nog niet ondersteund';
  test('throws ProviderNotSupportedError on all methods', async () => {
    await expectAllMethodsThrow(adapter, PlaytvError, message);
  });
});

describe('ProviderRegistry includes stub adapters', () => {
  test('registry getAll contains both adapters', async () => {
    const registry = ProviderRegistry.getInstance();
    // Register adapters for test isolation
    await registry.register(new VtmgoProviderAdapter());
    await registry.register(new PlaytvProviderAdapter());
    const all = registry.getAll().map((a) => a.name);
    expect(all).toEqual(expect.arrayContaining(['vtmgo', 'playtv']));
  });
});
