# botstop

TypeScript/JavaScript client for the [BotStop](https://github.com/MilitantAI/BotStop) HTTP API.

## Install

```bash
pnpm add botstop
# or
npm install botstop
```

## Usage

```ts
import { BotStopClient, mountBotStopWidget } from "botstop";

const client = new BotStopClient({
  baseUrl: "http://127.0.0.1:8787",
  apiKey: process.env.BOTSTOP_API_KEY,
});

const challenge = await client.createChallenge();
console.log(challenge.gif_url);

const result = await client.verifyChallenge(challenge.challenge_id, "4829");
```

## Drop-in widget

```ts
import { BotStopClient, mountBotStopWidget } from "botstop";

const client = new BotStopClient({ baseUrl: "http://127.0.0.1:8787" });

mountBotStopWidget(client, {
  target: document.getElementById("captcha")!,
  onVerified: (result) => {
    if (result.ok) submitForm();
  },
});
```

## API

- `BotStopClient` — `createChallenge()`, `refreshChallenge(previousId?)`, `verifyChallenge(id, answer)`
- `mountBotStopWidget(client, options)` — minimal UI with refresh + verify
