export class VrtUrlError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "VrtUrlError";
  }
}

export interface VrtUrlComponents {
  show: string;
  season: number;
  episodeCode: string;
}

export function parseVrtUrl(url: string): VrtUrlComponents {
  const regex = /\/vrtmax\/a-z\/([^/]+)\/(\d+)\/([^/]+)\/?$/;
  const match = url.match(regex);

  if (!match) {
    throw new VrtUrlError(
      `Invalid VRT MAX URL: ${url}. Expected format: /vrtmax/a-z/{show}/{season}/{episode-id}/`,
    );
  }

  return {
    show: match[1]!,
    season: parseInt(match[2]!, 10),
    episodeCode: match[3]!,
  };
}
