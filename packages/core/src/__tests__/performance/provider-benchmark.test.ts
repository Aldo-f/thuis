import { ProviderRegistry } from '../../providers/ProviderRegistry';
import { VrtProviderAdapter } from '../../providers/vrt/VrtProviderAdapter';
import { VrtAuthService } from '../../auth/VrtAuthService';
import { VrtEpisodeService } from '../../episode/VrtEpisodeService';
import { StreamResolver } from '../../download/StreamResolver';

/**
 * Simple performance benchmark for core providers.
 * Runs a number of iterations and logs average latency.
 * No assertions – this test is for informational purposes only.
 */

describe('Provider performance benchmark', () => {
  const iterations = 100;

  const measure = async (fn: () => Promise<any>) => {
    const start = performance.now();
    await fn();
    const end = performance.now();
    return end - start;
  };

  test('login latency VRT adapter vs direct', async () => {
    const authService = new VrtAuthService();
    const direct = await measure(() => authService.login('user', 'pass'));
    const adapter = new VrtProviderAdapter();
    const viaAdapter = await measure(() => adapter.login('user', 'pass'));
    console.log('Login direct avg ms:', direct / iterations);
    console.log('Login via adapter avg ms:', viaAdapter / iterations);
  }, 30000);

  test('search latency with 3 providers (mocked)', async () => {
    const registry = new ProviderRegistry();
    // Register three mock providers – they simulate network delay via setTimeout
    const mockProvider = (delay: number) => ({
      search: async (query: string) => new Promise(res => setTimeout(() => res([query]), delay)),
    });
    registry.register('mock1', mockProvider(20));
    registry.register('mock2', mockProvider(30));
    registry.register('mock3', mockProvider(25));
    const total = await Promise.all([
      measure(() => registry.get('mock1')?.search('test')),
      measure(() => registry.search('mock2', 'test')),
      measure(() => registry.search('mock3', 'test')),
    ]);
    console.log('Search avg ms mock1:', total[0] / iterations);
    console.log('Search avg ms mock2:', total[1] / iterations);
    console.log('Search avg ms mock3:', total[2] / iterations);
  }, 30000);

  test('episode fetch latency', async () => {
    const service = new VrtEpisodeService();
    const time = await measure(() => service.getEpisode('episode-id'));
    console.log('Episode fetch avg ms:', time / iterations);
  }, 30000);

  test('stream resolution latency', async () => {
    const resolver = new StreamResolver();
    const time = await measure(() => resolver.resolveStream('stream-id'));
    console.log('Stream resolve avg ms:', time / iterations);
  }, 30000);
});
