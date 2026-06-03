export interface Challenge {
  challenge_id: string;
  gif_url: string;
  digit_length: number;
  expires_in: number;
}

export interface VerifyResult {
  ok: boolean;
  reason: string;
}

export interface BotStopClientOptions {
  baseUrl: string;
  apiKey?: string;
  fetchImpl?: typeof fetch;
}

export interface MountWidgetOptions {
  target: HTMLElement;
  onVerified?: (result: VerifyResult) => void;
  onError?: (error: Error) => void;
  labels?: {
    prompt?: string;
    placeholder?: string;
    submit?: string;
    refresh?: string;
  };
}
