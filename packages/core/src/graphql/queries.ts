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

/**
 * VideoPage query — fetches episode metadata from a VRT MAX URL path.
 * This is the primary query used by the new VRT MAX frontend.
 * The pageId variable is the URL path: e.g. "/vrtmax/a-z/thuis/31/thuis-s31a6105/"
 */
export const VIDEO_PAGE_QUERY = `
query VideoPage($pageId: ID!) {
  page(id: $pageId) {
    ... on EpisodePage {
      episode {
        ageRaw
        description
        durationRaw
        episodeNumberRaw
        id
        name
        onTimeRaw
        program {
          title
        }
        season {
          id
          titleRaw
        }
        title
        brand
      }
      ldjson
      player {
        image {
          templateUrl
        }
        modes {
          streamId
        }
      }
    }
  }
}`;
