import { SearchService } from "../../../src/services/SearchService.ts";
import type { ProviderAdapter, SearchResult } from "@thuis/core";

jest.mock("@thuis/core", () => {
  const actual = jest.requireActual("@thuis/core");
  return {
    ...actual,
    ProviderRegistry: {
      getInstance: () => ({
        getAll: jest.fn()
      })
    }
  };
});

const { ProviderRegistry } = require("@thuis/core");

function createAdapter(id: string, supportsSearch: boolean, results: SearchResult[], reject = false): ProviderAdapter {
  return {
    name: id,
    id,
    displayName: id,
    supportsSearch,
    supportsAuth: false,
    async init() {},
    async dispose() {},
    async login() { return { accessToken: "t" }; },
    async search() {
      if (reject) throw new Error("fail");
      return results;
    },
    async getEpisode() { return { id: "e", title: "e" }; },
    async resolveStream() { return { url: "" } as any; }
  } as ProviderAdapter;
}

describe("SearchService", () => {
  const service = new SearchService();

  afterEach(() => {
    jest.clearAllMocks();
  });

  it("fans out to all searchable providers and adds provider field", async () => {
    const adapters = [
      createAdapter("p1", true, [{ id: "1", title: "One" }]),
      createAdapter("p2", true, [{ id: "2", title: "Two" }])
    ];
    ProviderRegistry.getInstance().getAll.mockReturnValue(adapters);
    const results = await service.search("test");
    expect(results).toHaveLength(2);
    expect(results).toEqual([
      { id: "1", title: "One", provider: "p1" },
      { id: "2", title: "Two", provider: "p2" }
    ]);
  });

  it("returns partial results when a provider fails", async () => {
    const adapters = [
      createAdapter("good", true, [{ id: "1", title: "One" }]),
      createAdapter("bad", true, [], true)
    ];
    ProviderRegistry.getInstance().getAll.mockReturnValue(adapters);
    const results = await service.search("test");
    expect(results).toHaveLength(1);
    expect(results[0]).toMatchObject({ id: "1", provider: "good" });
  });

  it("filters out providers that do not support search", async () => {
    const adapters = [
      createAdapter("search", true, [{ id: "1", title: "One" }]),
      createAdapter("nosrch", false, [{ id: "2", title: "Two" }])
    ];
    ProviderRegistry.getInstance().getAll.mockReturnValue(adapters);
    const results = await service.search("test");
    expect(results).toHaveLength(1);
    expect(results[0].provider).toBe("search");
  });

  it("returns empty array when no providers are searchable", async () => {
    ProviderRegistry.getInstance().getAll.mockReturnValue([]);
    const results = await service.search("test");
    expect(results).toEqual([]);
  });
});
