# OpenAI Toolset for TypeScript

Run a GPT browser task with the OpenAI SDK and the `stagehand-openai-sdk` npm package. This example opens `example.com` in a visible Chrome window and asks the model what the page says.

## Prerequisites

- Node.js 22.18 or later and pnpm.
- Google Chrome for local execution, or a Browserbase API key for a hosted browser.
- An OpenAI API key with access to `gpt-5.5`, or another model you set with `OPENAI_MODEL`.

## Install and run

Run these commands from this repository's `typescript` directory:

```bash
pnpm install
cp .env.example .env
# Set OPENAI_API_KEY in .env (and OPENAI_MODEL to use a model other than gpt-5.5)
pnpm example
```

The example prints the model's final answer. Look for a response quoting the page's heading, **Example Domain**, and its text about documentation examples.

## How the example works

[example.ts](example.ts) launches a `StagehandBrowserDriver`, wraps it in OpenAI's `BrowserToolset` with `createBrowserToolset`, hands the toolset to the SDK's `ResponsesToolRunner`, and closes everything in `finally`:

```typescript
import OpenAI from "openai";
import { ResponsesToolRunner } from "openai/helpers/responses-tool-runner";
import {
  StagehandBrowserDriver,
  createBrowserToolset,
} from "stagehand-openai-sdk";

const driver = await StagehandBrowserDriver.launch({
  headless: false,
  allowedDomains: ["example.com", "iana.org"],
  webrtc: "allow",
});

const browser = createBrowserToolset(driver);

try {
  const runner = new ResponsesToolRunner({ browser: browser.toolset });
  const response = await runner.run(
    new OpenAI(),
    {
      model: process.env.OPENAI_MODEL ?? "gpt-5.5",
      store: false,
      input: "Open example.com and tell me what the page says",
    },
    { maxSteps: 20 },
  );
  console.log(response.output_text);
} finally {
  await browser.close();
}
```

- `createBrowserToolset(driver)` returns `{ toolset, members, confirm, urlPolicy, close }`. With no options it advertises the default members, derives a `urlPolicy` from the domain lists, and uses the default `confirm`, which approves every default member while the browser is alive.
- `browser.close()` stops the toolset, then closes the driver and only what the driver created (the Chrome process here).
- `webrtc: "allow"` turns off an experimental WebRTC guard that is being removed from the driver.

Edit the task in `input`, or set `OPENAI_MODEL` in `.env` to change the model. Set `headless: true` to run without a visible Chrome window, and update `allowedDomains` for your task's websites.

## Use Browserbase

Set `BROWSERBASE_API_KEY` in your `.env` file.

Replace the `StagehandBrowserDriver.launch` call in `example.ts` with:

```typescript
const apiKey = process.env.BROWSERBASE_API_KEY;
if (!apiKey) throw new Error("Set BROWSERBASE_API_KEY before running this example.");

const driver = await StagehandBrowserDriver.browserbase({
  apiKey,
  allowedDomains: ["example.com", "iana.org"],
  webrtc: "allow",
});
```

Keep the runner and `finally` block, then run `pnpm example` again. Browserbase creates the browser session, so you don't need local Chrome. `browser.close()` releases the session.

## Enable optional tools

The default members cover reading, clicking, typing, forms, screenshots, tabs and waits. The rest are opt-ins:

| Member | What it adds | Needs your own `confirm` |
| --- | --- | --- |
| `click_at`, `hover_at`, `drag_path`, `hold_keys` | Pointer and keyboard by viewport coordinates, for canvases and custom widgets | no |
| `read_page_scoped` | Lists page scopes (landmarks, forms, dialogs, tables, iframes) and reads one subtree | no |
| `set_checked` | Sets a checkbox or radio to a state, idempotently | no |
| `run_script` | Runs JavaScript in the page | yes |
| `upload_file` / `download_file` | Moves files through single-use grants your code resolves | yes |
| `read_diagnostics` | Redacted console and network lines | yes |

Add opt-ins with `additionalMembers`, or pass the exact set with `members` (not both):

```typescript
const driver = await StagehandBrowserDriver.launch({
  headless: false,
  allowedDomains: ["example.com"],
  webrtc: "allow",
  uploads: {
    roots: ["/absolute/path/to/uploads"], // upload_file reads only files under these directories
    resolveGrant: async (grantId) => (grantId === "report" ? { path: "/absolute/path/to/uploads/report.pdf" } : null),
  },
});

const browser = createBrowserToolset(driver, {
  additionalMembers: ["click_at", "set_checked", "run_script", "upload_file"],
  confirm: async (ctx) => {
    // Called before every browser tool call. Return false to refuse that call.
    if (ctx.member === "run_script" || ctx.member === "upload_file") {
      return askAPerson(ctx.member, ctx.arguments); // your UI or policy
    }
    return true;
  },
});
```

- **`confirm` is required** for `run_script`, `upload_file`, `download_file` and `read_diagnostics`; `createBrowserToolset` throws without it. Your `confirm` replaces the default for every member, including navigation and clicks, so return `true` for the routine ones.
- **`run_script` runs with the page's own cookies and sessions.** Use a browser profile that isn't signed in to accounts you wouldn't hand the model.
- **Files move through grants.** Tell the model which grant ids it may use (in your instructions); your `resolveGrant` turns an id into a file or refuses it with `null`. Grants are single use. For downloads, pass `downloads: { resolveGrant }`; files land in a quarantine directory and reach your disk only through the grant's `deliver` callback (local browsers only).
- **`read_diagnostics`** turns on the console and network buffers and drops entries from origins the domain policy refuses.

## Use in your own project

Install the packages in your TypeScript project:

```bash
pnpm add openai@7.33.0 stagehand-openai-sdk
```

`openai` is a peer dependency of `stagehand-openai-sdk`. Keep a single copy of it in your dependency tree: the driver reports refusals with the SDK's own error class. Use the imports and runner above with an ESM-compatible TypeScript runner. This repository uses `tsx` through its `example` script.

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Missing API key | Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. |
| Model access error | Set `OPENAI_MODEL` in `.env` to a model your account can use. |
| Chrome doesn't launch | Install Google Chrome or pass `chromePath` to `launch`. |
| Navigation is blocked | Check `allowedDomains` and `blockedDomains`. The model sees `blocked: not in allowed domains (<host>)`. |
| Every tool call fails with "Browser operation failed." | Two copies of `openai` are installed. Run `pnpm why openai` and dedupe to one. |
| Missing package exports | Check that the installed `openai` release provides `openai/helpers/browser` and `openai/helpers/responses-tool-runner` (7.33.0 or later). |

See the [shared limitations](../README.md#limitations) for domain filtering, dialogs and Browserbase downloads, or return to the [repository overview](../README.md).
