import { BotStopClient } from "./client.js";
import type { Challenge, MountWidgetOptions } from "./types.js";

export function mountBotStopWidget(
  client: BotStopClient,
  options: MountWidgetOptions,
): { refresh: () => Promise<void>; getChallengeId: () => string | null } {
  const labels = {
    prompt: "Watch the static and enter the digits you see.",
    placeholder: "Enter digits",
    submit: "Verify",
    refresh: "Refresh",
    ...options.labels,
  };

  let current: Challenge | null = null;
  const root = options.target;
  root.innerHTML = `
    <div class="botstop-widget" style="display:grid;gap:12px;font-family:system-ui,sans-serif;">
      <p style="margin:0;color:#bbb;">${labels.prompt}</p>
      <img alt="BotStop captcha" style="width:100%;max-width:480px;background:#000;border-radius:8px;" />
      <div style="display:flex;gap:8px;flex-wrap:wrap;">
        <input inputmode="numeric" pattern="[0-9]*" autocomplete="off" spellcheck="false"
          placeholder="${labels.placeholder}"
          style="flex:1;min-width:180px;padding:10px 12px;border-radius:8px;border:1px solid #444;background:#111;color:#fff;" />
        <button type="button" data-action="verify" style="padding:10px 14px;border:0;border-radius:8px;background:#3d7eff;color:#fff;cursor:pointer;">${labels.submit}</button>
        <button type="button" data-action="refresh" style="padding:10px 14px;border:1px solid #444;border-radius:8px;background:#222;color:#fff;cursor:pointer;">${labels.refresh}</button>
      </div>
      <div data-role="status" style="min-height:1.25rem;color:#bbb;"></div>
    </div>
  `;

  const image = root.querySelector("img") as HTMLImageElement;
  const input = root.querySelector("input") as HTMLInputElement;
  const status = root.querySelector('[data-role="status"]') as HTMLDivElement;
  const verifyButton = root.querySelector('[data-action="verify"]') as HTMLButtonElement;
  const refreshButton = root.querySelector('[data-action="refresh"]') as HTMLButtonElement;

  async function loadChallenge(previousId?: string): Promise<void> {
    status.textContent = "";
    input.value = "";
    current = previousId
      ? await client.refreshChallenge(previousId)
      : await client.createChallenge();
    image.src = `${current.gif_url}?t=${Date.now()}`;
    input.maxLength = current.digit_length;
  }

  verifyButton.addEventListener("click", async () => {
    if (!current) {
      return;
    }
    try {
      const result = await client.verifyChallenge(current.challenge_id, input.value.trim());
      status.textContent = result.ok ? "Verified." : `Not verified (${result.reason}).`;
      status.style.color = result.ok ? "#6dffb0" : "#ff7b7b";
      options.onVerified?.(result);
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      status.textContent = err.message;
      status.style.color = "#ff7b7b";
      options.onError?.(err);
    }
  });

  refreshButton.addEventListener("click", () => {
    void loadChallenge(current?.challenge_id).catch((error) => {
      const err = error instanceof Error ? error : new Error(String(error));
      options.onError?.(err);
    });
  });

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      verifyButton.click();
    }
  });

  void loadChallenge().catch((error) => {
    const err = error instanceof Error ? error : new Error(String(error));
    options.onError?.(err);
  });

  return {
    refresh: () => loadChallenge(current?.challenge_id),
    getChallengeId: () => current?.challenge_id ?? null,
  };
}
