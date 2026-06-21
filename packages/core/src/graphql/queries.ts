export const SEARCH_EPISODES_QUERY = `
query component($componentId: ID!, $lazyItemCount: Int = 10, $after: ID) {
  component(id: $componentId) {
    ... on PaginatedTileList {
      title
      paginatedItems(first: $lazyItemCount, after: $after) {
        edges {
          node {
            __typename
            ... on EpisodeTile {
              title
              description
              image { templateUrl }
              action { ... on LinkAction { link } }
              primaryMeta { type value }
              secondaryMeta { type value }
              objectId
            }
          }
        }
        pageInfo { endCursor hasNextPage hasPreviousPage startCursor }
      }
    }
  }
}`;

export const EPISODE_BY_URL_QUERY = `
query component($componentId: ID!) {
  component(id: $componentId) {
    ... on PaginatedTileList {
      paginatedItems(first: 1) {
        edges { node { ...EpisodeTileFragment } }
      }
    }
  }
}

fragment EpisodeTileFragment on EpisodeTile {
  title
  description
  image { templateUrl }
  action { ... on LinkAction { link } }
  primaryMeta { type value }
  secondaryMeta { type value }
  objectId
}`;
