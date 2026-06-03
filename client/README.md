# botstop

TypeScript/JavaScript client for the [BotStop](https://github.com/MilitantAI/BotStop) HTTP API.

## Install

```bash
npm install botstop
```

## Usage

Point `baseUrl` at your deployed BotStop API (HTTPS in production):

```ts
import { BotStopClient, mountBotStopWidget } from "botstop";

const client = new BotStopClient({
  baseUrl: "https://api.yourdomain.com",
  apiKey: process.env.BOTSTOP_API_KEY,
});

mountBotStopWidget(client, {
  target: document.getElementById("captcha")!,
  onVerified: (result) => {
    if (result.ok) submitForm();
  },
});
```

Server setup: see the [BotStop README](https://github.com/MilitantAI/BotStop#deploy).

## API

- `BotStopClient` — `createChallenge()`, `refreshChallenge(previousId?)`, `verifyChallenge(id, answer)`
- `mountBotStopWidget(client, options)` — minimal UI with refresh + verify
