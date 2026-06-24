// Integration test for VRT provider flow
// This test registers the VRT adapter, locks/unlocks the credential vault,
// logs in using mocked credentials, fetches an episode and resolves a stream.
// All external HTTP calls are mocked with nock.

import { ProviderRegistry } from '../../providers/ProviderRegistry.js';
import { VrtProviderAdapter } from '../../providers/vrt/VrtProviderAdapter.js';
import { CredentialVault } from '../../vault/Vault.js';
import nock from 'nock';

// Helper to create a fresh vault instance for each test
function createVault() {
  const vault = new CredentialVault();
  // Use a test password; not read from env to keep CI deterministic
  const password = 'test-password';
  // Lock and then unlock to initialize internal state
  vault.lock();
  vault.unlock(password);
  return { vault, password };
}

describe('VRT provider integration flow', () => {
  const originalEnv = {...process.env};
  const mockUsername = 'testuser';
  const mockPassword = 'testpass';
  const mockEpisodeId = '12345';
  const mockStreamUrl = 'https://stream.example.com/video.m3u8';

  beforeAll(() => {
    // Preserve original env and clear VRT vars so test uses stored credentials
    process.env = { ...originalEnv };
    delete process.env.VRT_USERNAME;
    delete process.env.VRT_PASSWORD;
  });

  afterAll(() => {
    process.env = originalEnv;
    nock.cleanAll();
    nock.restore();
  });

  it('should login, fetch episode and resolve stream using mocked HTTP calls', async () => {
    // ---------- Setup mocks ----------
    // Mock VRT authentication endpoint
    nock('https://services.vrt.be')
      .post('/auth/login', {
        username: mockUsername,
        password: mockPassword,
      })
      .reply(200, { token: 'fake-jwt-token' });

    // Mock episode lookup endpoint
    nock('https://services.vrt.be')
      .get(`/episodes/${mockEpisodeId}`)
      .reply(200, {
        id: mockEpisodeId,
        title: 'Test Episode',
        streamId: 'stream-123',
      });

    // Mock stream resolver endpoint
    nock('https://services.vrt.be')
      .get('/streams/stream-123')
      .reply(200, { url: mockStreamUrl });

    // ---------- Prepare vault ----------
    const { vault, password } = createVault();
    // Store credentials in the vault under the VRT provider key
    await vault.addCredentials('vrt', mockUsername, mockPassword);

    // ---------- Register provider ----------
    const registry = ProviderRegistry.getInstance();
    const vrtAdapter = new VrtProviderAdapter(vault);
    registry.registerProvider('vrt', vrtAdapter);

    // ---------- Execute flow ----------
    // Provider should read credentials from the vault, perform login, then fetch episode and resolve stream
    const provider = registry.getProvider('vrt');
    // Login using stored credentials (the adapter internally reads from the vault)
    await provider.login();

    // Fetch episode metadata
    const episode = await provider.getEpisode(mockEpisodeId);
    expect(episode.id).toBe(mockEpisodeId);
    expect(episode.title).toBe('Test Episode');

    // Resolve stream URL
    const stream = await provider.resolveStream(episode.streamId);
    expect(stream.url).toBe(mockStreamUrl);
  });
});
