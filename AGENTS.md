# AGENTS.md

Instructions for coding agents (Codex, Claude Code, Cursor, and others) helping someone set up and try this repository. The goal: from a fresh clone to watching a GPT model drive a browser on a task the user picked, in a few minutes, with the user in control of their credentials.

This repository shows how to give GPT a browser through the OpenAI SDK. `StagehandBrowserDriver`, from the `stagehand-openai-sdk` package, implements the driver contract of OpenAI's browser toolset (`BrowserToolset` in TypeScript, `AsyncBrowserToolset` in Python) on top of Stagehand. The driver's `createBrowserToolset` / `create_browser_toolset` builder wraps it in that toolset, and the OpenAI SDK's Responses tool runner handles the model loop. There is one example per language:

| | TypeScript | Python |
| --- | --- | --- |
| Directory | `typescript/` | `python/` |
| Example | `typescript/example.ts` | `python/example.py` |
| Requires | Node.js 22.18+, pnpm | Python 3.11+, uv |
| Run | `pnpm example` | `uv run --env-file .env python example.py` |

## How to work with the user

- **Do the work, ask only for decisions.** Run the checks and installs yourself. Ask the user only about what is theirs to decide: the language, local Chrome or Browserbase, their API keys, the model, and the task to try.
- **Never read, print, or paste secrets.** Don't `cat` a `.env` file or echo key values. Ask the user to paste keys into `.env` themselves, then check that a key is present without showing it (see step 3).
- **Say what will happen before it happens.** The examples open a visible Chrome window by default so the user can watch the model work. Tell them a window will appear, and that each run calls the OpenAI API and is billed to their key.
- **Keep the user in the loop on the task.** Don't point the browser at sites that need the user's accounts, purchases, or personal data unless the user explicitly asks for it.

## Setup

### 1. Pick a language and a browser

Ask which language they prefer. If they have no preference, use the one their machine already has tooling for. Prefer TypeScript if both are present.

Ask where the browser should run:

- **Local Chrome:** the default. Requires Google Chrome, or another Chromium-based browser passed as `chromePath` / `chrome_path`. Firefox and Safari are not supported.
- **Browserbase:** a hosted browser, so no local Chrome is needed. Requires a Browserbase API key from https://www.browserbase.com.

### 2. Check prerequisites

Run the checks for the chosen language and fix what is missing, asking before installing anything system-wide.

```bash
# TypeScript
node --version     # needs v22.18.0 or later
pnpm --version     # if missing: corepack enable pnpm   (or npm install -g pnpm)

# Python
uv --version       # if missing: see https://docs.astral.sh/uv/getting-started/installation/
                   # uv installs a matching Python for the project if needed

# Local Chrome (skip for Browserbase)
ls "/Applications/Google Chrome.app" 2>/dev/null           # macOS
command -v google-chrome chromium chromium-browser         # Linux
```

If Chrome isn't installed and the user doesn't want to install it, offer Browserbase instead.

### 3. Install and add credentials

```bash
cd typescript && pnpm install       # or: cd python && uv sync
cp .env.example .env
```

Ask the user to open `.env` and set `OPENAI_API_KEY`, plus `BROWSERBASE_API_KEY` if they chose Browserbase. The example runs `gpt-5.5` unless `OPENAI_MODEL` is set; ask which model they want and, if it isn't `gpt-5.5`, have them uncomment `OPENAI_MODEL` in `.env` and set it. Keys come from https://platform.openai.com/api-keys and https://www.browserbase.com. `.env` is gitignored in both directories.

Confirm that a key is set without printing it. This prints only a count; `1` means the key is present:

```bash
grep -c '^OPENAI_API_KEY=..' .env
```

### 4. Switch to Browserbase (only if chosen)

Replace the `StagehandBrowserDriver.launch(...)` call in the example with the Browserbase variant shown in that language's README ("Use Browserbase" section). Keep `allowedDomains` / `allowed_domains` and `webrtc`. Everything else stays the same.

### 5. Run the example

```bash
pnpm example                                    # typescript/
uv run --env-file .env python example.py        # python/
```

Expected result: a Chrome window opens on `example.com`, the model reads the page, and the printed answer quotes the heading **Example Domain** and the text about documentation examples. The run takes well under a minute. The browser closes on its own when the run ends.

If it fails, check the troubleshooting table below before changing code.

## Try it out

Once the example passes, offer to run a task of the user's choosing. Change three things in the example file:

1. **The task:** the `input` string.
2. **The allowed domains:** every site the task needs. An entry covers its subdomains, so `wikipedia.org` allows `en.wikipedia.org`. Navigation to any other site is refused with `blocked: not in allowed domains (<host>)`, which keeps the model on task.
3. **The step limit:** `maxSteps` / `max_steps` caps model turns. 20 is enough for most short tasks; raise it to 40 or more for long multi-page tasks.

Starter tasks that need no login:

| Task | Allowed domains |
| --- | --- |
| "Go to Hacker News and list the top five stories with their points." | `news.ycombinator.com` |
| "Find the Wikipedia article on the Apollo 11 mission and tell me the landing date and crew." | `wikipedia.org` |
| "Search GitHub for the browserbase/stagehand repository and report its star count and latest release." | `github.com` |
| "Open the Python documentation and summarize what's new in the latest release." | `python.org` |

Let the user watch the window. The example prints only the final answer (`output_text`). To show the tool calls the model made (navigate, read_page, find, click, type, screenshot), print `response.output` instead.

To run Chrome without a window, for example on a server or in CI, set `headless: true` (TypeScript) or `headless=True` (Python).

## Use it in the user's own project

```bash
pnpm add openai@7.33.0 stagehand-openai-sdk             # TypeScript (openai is a peer dependency)
uv add 'openai>=3.31.0' stagehand-openai-sdk            # Python (import as stagehand_openai_sdk)
```

The pattern is the same as the example:

- Create one `StagehandBrowserDriver` per task with `launch`, `connect` or `browserbase`.
- Build the toolset with `createBrowserToolset(driver, options?)` / `create_browser_toolset(driver, ...)`. It returns a bundle: `toolset`, `members`, `confirm`, `urlPolicy` / `url_policy`, and `close()`.
- Pass `bundle.toolset` as `browser` to `new ResponsesToolRunner({ browser })` / `AsyncResponsesToolRunner(browser=...)`, then call `runner.run(client, { model, store: false, input }, { maxSteps })`.
- Close the bundle in `finally`. It stops the toolset, then closes the driver and only what the driver created. The tool runner never closes it.

The Python driver is async only, so use `AsyncOpenAI` and `AsyncResponsesToolRunner`. In TypeScript keep a single copy of `openai` in the dependency tree: the driver raises the SDK's own error class, and a second copy turns every refusal into a generic failure.

Builder options (camelCase in TypeScript, snake_case in Python):

| Option | Purpose |
| --- | --- |
| `members` | The exact member set the model sees. Mutually exclusive with `additionalMembers`. |
| `additionalMembers` | Opt-ins added to the defaults, such as `click_at`, `set_checked`, `read_page_scoped`, `run_script`. |
| `confirm` | Your consent hook, called before every browser tool call; return `false` to refuse. Without it the default `confirm` is used: it approves the default members while the browser is alive and the tab exists. It is a liveness check, not human consent. |
| `urlPolicy` | Your own URL check, AND-ed with the policy derived from the domain lists. The driver's verdict runs first, so the model gets the specific refusal. |

Useful options for `StagehandBrowserDriver.launch`:

| Option | Purpose |
| --- | --- |
| `allowedDomains` / `blockedDomains` | Restrict where the browser may go, enforced inside the browser. Blocked entries win. |
| `webrtc` | Keep `"allow"`, as in the examples. It turns off an experimental WebRTC guard that is being removed. |
| `headless` | `false` to watch, `true` for servers. |
| `chromePath` | Use a specific Chromium-based browser. |
| `viewport` | Page size for screenshots and coordinates (default 1280x720). |
| `maskSelectors` | Elements painted over in every screenshot. |

`StagehandBrowserDriver.connect({ cdpUrl })` drives a Chromium that is already running; `StagehandBrowserDriver.browserbase({ apiKey })` creates a hosted session and releases it on close.

## Turn on optional tools

`click_at`, `hover_at`, `drag_path`, `hold_keys`, `set_checked` and `read_page_scoped` are off by default; add them with `additionalMembers` / `additional_members` when a task needs them (canvases, custom widgets, long pages). `run_script`, `upload_file`, `download_file` and `read_diagnostics` reach further, so ask the user first: `run_script` runs JavaScript with the page's cookies and sessions, and the file members move files between the user's machine and the browser. All four require the user's own `confirm` callback (the builder refuses to select them without one), and the file members also need `uploads` / `downloads` grant resolvers. The "Enable optional tools" section of each language README has the exact code.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Authentication error or missing key | `OPENAI_API_KEY` isn't set in `.env`. Re-check with the `grep -c` command above. |
| Model not found or not permitted | The account can't use the model. Ask the user which OpenAI model they have access to and set `OPENAI_MODEL` in `.env`. |
| `model` is empty or invalid | `OPENAI_MODEL=` is present but blank in `.env`. Set it or comment it out. |
| Chrome doesn't launch | Install Google Chrome, pass `chromePath` / `chrome_path`, or switch to Browserbase. |
| `blocked: not in allowed domains` in the answer | The site isn't in the allowed domains. Add it and rerun. |
| Every tool call fails with "Browser operation failed." (TypeScript) | Two copies of `openai` are installed. Dedupe to one (`pnpm why openai`). |
| Package exports or attributes missing | The installed OpenAI SDK predates the browser toolset helpers. Reinstall with `pnpm install` or `uv sync`. |
| `TypeError` or throw when selecting `run_script` / file members | Pass your own `confirm`. |
| The run stops before answering | It hit the step limit. Raise `maxSteps` / `max_steps`. |
| Browser connection lost mid-run | Close the bundle and create a new driver; a session isn't reused after its browser dies. |
| Downloads don't appear on Browserbase | Expected: `download_file` isn't available in Browserbase sessions. |

## Why Stagehand as the driver

OpenAI's browser toolset defines what the model can do in a browser. A driver supplies the browser underneath. OpenAI doesn't ship a general-purpose driver: its examples include two narrow reference drivers, a three-page reader and the one-form booking adapter behind its Fieldwork demo. Each implements at most 7 of the toolset's 28 members and works only on its own fixture. `StagehandBrowserDriver` is the same toolset on Stagehand, Browserbase's open-source browser automation runtime, and it implements every member in both TypeScript and Python.

### Where it does more than the reference drivers

- **Every toolset member, not a subset.** Besides reading, clicking, typing and select boxes, Stagehand covers keys, scrolling, hover, screenshots and zoom, tabs, waits, and the opt-ins (coordinate input, checkboxes, scoped reads, scripts, files, diagnostics) that real tasks need.
- **The whole page is visible.** `read_page`, `find` and `get_page_text` cover every frame, including cross-origin iframes and nested framesets, and open shadow DOM. Embedded checkout forms, payment widgets and web components are listed and actionable.
- **Stable element references.** A ref names a specific node in a specific document. Refs survive actions that don't navigate, so the model can fill several fields in one turn. A ref from an older document or another tab is refused instead of clicking whatever now sits in that spot, and before a mutating action the driver checks the element still has the role and name it was read with.
- **The page doesn't get stuck.**
  - JavaScript dialogs are answered and reported to the model instead of freezing the page.
  - Popups and `target=_blank` links show up as new tabs, and downloads are reported.
  - After a click that loads a new page, the driver waits for the navigation before the model reads again.
- **Domain restrictions enforced inside the browser.** Allowed and blocked domains apply to navigations, redirects, sub-resources, popups, workers and WebSocket handshakes, not just the URLs the model types, and every refusal reaches the model as a fixed phrase that names the host.
- **One driver for local and hosted.** The same class launches local Chrome, attaches to a running Chromium, or opens a Browserbase session, with privacy masking, OpenTelemetry spans and bounded timeouts on every call.

### Performance and cost

**Head-to-head on OpenAI's Fieldwork task.** The `reservation` task, graded by OpenAI's own verifier (the submitted record and the visible form must both match). Same harness for both drivers: `ResponsesToolRunner`, the same six members, a 24-step budget, headless local Chrome, a fresh browser per trial, priced at list.

| Model | Driver | Verified | Median steps | Median time per task | Mean cost per task | Failed tool calls per run |
| --- | --- | --- | --- | --- | --- | --- |
| GPT-5.5 | Stagehand | **10 / 10** | **6** | **12.0 s** | **$0.058** | **0.0** |
| GPT-5.5 | OpenAI reference driver | 10 / 10 | 12 | 22.1 s | $0.115 | 2.4 |

- **Half the steps and half the cost, about 45% less wall time, at the same success rate.** The reference driver invalidates every ref after each action, so the model's batched turn (type a name, pick three options) fails after the first call and it has to re-read between fields. Stagehand refs survive non-navigating actions, so the batch lands in one turn.
- **Fewer tokens:** 23,685 input and 405 output tokens per run on average, against 42,398 and 944.
- Fieldwork has a single task, and the reference driver is fit to it, so this is a parity check on the reference's home ground rather than a capability test.

**Live websites.** Eight public, login-free tasks with GPT-5.5, checked by the harness (answer patterns and page state, never an LLM judge), run on three lanes with a 20-step budget and the default members:

| Lane | Tasks passed | Steps (total) | Wall time (total) |
| --- | --- | --- | --- |
| TypeScript, local Chrome | 7 / 8 | 66 | 343 s |
| TypeScript, Browserbase | 7 / 8 | 72 | 293 s |
| Python, local Chrome | 7 / 8 | 67 | 172 s |

- The tasks cover framesets two levels deep, open and nested shadow DOM, a `target=_blank` popup, a native form with radios, checkboxes, a time input and a textarea, and JS-rendered pagination. The frames task is out of reach for the reference drivers.
- The one failure on every lane is the same task: it needs text typed into a `prompt()` dialog, which the browser dismisses automatically. With `run_script` opted in, it passes in 6 steps.
- Most of the wall time is the test site stalling single resources for about 30 seconds, reproducible with plain headless Chrome and no Stagehand. The driver reported each stall as a timeout and the model recovered.
