import type { BotStopClientOptions, Challenge, VerifyResult } from "./types.js";

function joinUrl(baseUrl: string, path: string): string {
  return `${baseUrl.replace(/\/+$/, "")}${path.startsWith("/") ? path : `/${path}`}`;
}

function headers(apiKey?: string): HeadersInit {
  const value: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (apiKey) {
    value["X-API-Key"] = apiKey;
  }
  return value;
}

export class BotStopClient {
  readonly baseUrl: string;
  readonly apiKey?: string;
  private readonly fetchImpl: typeof fetch;

  constructor(options: BotStopClientOptions) {
    this.baseUrl = options.baseUrl.replace(/\/+$/, "");
    this.apiKey = options.apiKey;
    this.fetchImpl = options.fetchImpl ?? fetch;
  }

  async createChallenge(): Promise<Challenge> {
    const response = await this.fetchImpl(joinUrl(this.baseUrl, "/v1/challenges"), {
      method: "POST",
      headers: headers(this.apiKey),
    });
    if (!response.ok) {
      throw new Error(`createChallenge failed: ${response.status}`);
    }
    const payload = (await response.json()) as Challenge;
    return {
      ...payload,
      gif_url: joinUrl(this.baseUrl, payload.gif_url),
    };
  }

  async refreshChallenge(previousId?: string): Promise<Challenge> {
    const response = await this.fetchImpl(joinUrl(this.baseUrl, "/v1/challenges/refresh"), {
      method: "POST",
      headers: headers(this.apiKey),
      body: JSON.stringify({ previous_id: previousId ?? null }),
    });
    if (!response.ok) {
      throw new Error(`refreshChallenge failed: ${response.status}`);
    }
    const payload = (await response.json()) as Challenge;
    return {
      ...payload,
      gif_url: joinUrl(this.baseUrl, payload.gif_url),
    };
  }

  async verifyChallenge(challengeId: string, answer: string): Promise<VerifyResult> {
    const response = await this.fetchImpl(
      joinUrl(this.baseUrl, `/v1/challenges/${encodeURIComponent(challengeId)}/verify`),
      {
        method: "POST",
        headers: headers(this.apiKey),
        body: JSON.stringify({ answer }),
      },
    );
    if (response.status === 404) {
      return { ok: false, reason: "not_found" };
    }
    if (!response.ok) {
      throw new Error(`verifyChallenge failed: ${response.status}`);
    }
    return (await response.json()) as VerifyResult;
  }
}
