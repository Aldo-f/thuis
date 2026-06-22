import { EpisodeDetailSchema, SearchResultSchema } from "../types/index.js";
import { SEARCH_EPISODES_QUERY, EPISODE_BY_URL_QUERY } from "./queries.js";
export function createClient(baseUrl, token) {
    const fetchGraphQL = async (query, variables) => {
        const response = await fetch(baseUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify({ query, variables }),
        });
        if (!response.ok) {
            throw new Error(`GraphQL request failed with status ${response.status}`);
        }
        const json = await response.json();
        if (json.errors && json.errors.length) {
            throw new Error(`GraphQL errors: ${json.errors.map((e) => e.message).join(", ")}`);
        }
        if (!json.data) {
            throw new Error("No data returned from GraphQL API");
        }
        return json.data;
    };
    const encodeComponentId = (payload) => {
        return Buffer.from(JSON.stringify(payload)).toString("base64");
    };
    return {
        async searchEpisodes(query, lazyItemCount = 10) {
            const componentId = encodeComponentId({ q: query });
            const variables = { componentId, lazyItemCount };
            const data = await fetchGraphQL(SEARCH_EPISODES_QUERY, variables);
            // Validate against Zod schema
            const parsed = SearchResultSchema.parse(data);
            return parsed;
        },
        async getEpisodeByUrl(url) {
            // Extract the episode code from URL using the resolver we already have
            // Imported lazily to avoid circular dependency
            const { parseVrtUrl } = await import("../url-resolver.js");
            const { episodeCode } = parseVrtUrl(url);
            const componentId = encodeComponentId({ componentId: episodeCode });
            const variables = { componentId };
            const data = await fetchGraphQL(EPISODE_BY_URL_QUERY, variables);
            const parsed = EpisodeDetailSchema.parse(data);
            return parsed;
        },
    };
}
