export interface LoginArgs {
  username: string;
  password: string;
}

export interface ProviderTokens {
  accessToken: string;
  refreshToken?: string;
}

export interface SearchResult {
  id: string;
  title: string;
  // Add other common properties as needed
}

export interface EpisodeDetail {
  id: string;
  title: string;
  // Add other episode details as needed
}

export interface StreamData {
  url: string;
  // Add other stream details as needed
}