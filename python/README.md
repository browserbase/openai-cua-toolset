# OpenAI Toolset for Python

Run an async GPT browser task with the OpenAI SDK and the `stagehand-openai-sdk` Python package. This example opens `example.com` in a visible Chrome window and asks the model what the page says.

## Prerequisites

- Python 3.11 or later and uv.
- Google Chrome for local execution, or a Browserbase API key for a hosted browser.
- An OpenAI API key with access to `gpt-6-luna`, or another model you set with `OPENAI_MODEL`.

## Install and run

Run these commands from this repository's `python` directory:

```bash
uv sync
cp .env.example .env
# Set OPENAI_API_KEY in .env (and OPENAI_MODEL to use a model other than gpt-6-luna)
uv run --env-file .env python example.py
```

The example prints the model's final answer. Look for a response quoting the page's heading, **Example Domain**, and its text about documentation examples.

## How the example works

[example.py](example.py) imports the published package as `stagehand_openai_sdk`, launches a `StagehandBrowserDriver`, wraps it in OpenAI's `AsyncBrowserToolset` with `create_browser_toolset`, hands the toolset to the SDK's `AsyncResponsesToolRunner`, and closes everything in `finally`:

```python
import asyncio
import os

from openai import AsyncOpenAI
from openai.lib.responses_tool_runner import AsyncResponsesToolRunner

from stagehand_openai_sdk import StagehandBrowserDriver, create_browser_toolset


async def main() -> None:
    driver = await StagehandBrowserDriver.launch(
        headless=False,
        allowed_domains=["example.com", "iana.org"],
    )
    browser = create_browser_toolset(driver)
    try:
        runner = AsyncResponsesToolRunner(browser=browser)
        response = await runner.run(
            AsyncOpenAI(),
            {
                "model": os.environ.get("OPENAI_MODEL", "gpt-6-luna"),
                "store": False,
                "input": "Open example.com and tell me what the page says",
            },
            max_steps=20,
        )
        print(response.output_text)
    finally:
        await driver.close()


if __name__ == "__main__":
    asyncio.run(main())
```

- `create_browser_toolset(driver)` returns OpenAI's `AsyncBrowserToolset`. With no options it advertises the default members, derives a `url_policy` from the domain lists, and uses the default `confirm`, which approves every default member while the browser is alive.
- `driver.close()` releases the browser, and only what the driver created (the Chrome process here). The toolset never closes the driver.
- The driver is async only, so it pairs with `AsyncOpenAI` and `AsyncResponsesToolRunner`.

Edit the task in `input`, or set `OPENAI_MODEL` in `.env` to change the model. Set `headless=True` to run without a visible Chrome window, and update `allowed_domains` for your task's websites.

## Use Browserbase

Set `BROWSERBASE_API_KEY` in your `.env` file.

Replace the `StagehandBrowserDriver.launch` call inside `main` with:

```python
driver = await StagehandBrowserDriver.browserbase(
    api_key=os.environ["BROWSERBASE_API_KEY"],
    allowed_domains=["example.com", "iana.org"],
)
```

Keep the runner and `finally` block, then run `uv run --env-file .env python example.py` again. Browserbase creates the browser session, so you don't need local Chrome. `driver.close()` releases the session.

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

Add opt-ins with `additional_members`, or pass the exact set with `members` (not both):

```python
from stagehand_openai_sdk import StagehandBrowserDriver, UploadOptions, create_browser_toolset


async def resolve_upload(grant_id: str, tab_id: str | None):
    return "/absolute/path/to/uploads/report.pdf" if grant_id == "report" else None


async def confirm(ctx: dict, **_) -> bool:
    # Called before every browser tool call. Return False to refuse that call.
    if ctx["member"] in ("run_script", "upload_file"):
        return await ask_a_person(ctx["member"], ctx["arguments"])  # your UI or policy
    return True


driver = await StagehandBrowserDriver.launch(
    headless=False,
    allowed_domains=["example.com"],
    # upload_file reads only files under these directories
    uploads=UploadOptions(roots=["/absolute/path/to/uploads"], resolve_grant=resolve_upload),
)
browser = create_browser_toolset(
    driver,
    additional_members=["click_at", "set_checked", "run_script", "upload_file"],
    confirm=confirm,
)
```

- **`confirm` is required** for `run_script`, `upload_file`, `download_file` and `read_diagnostics`; `create_browser_toolset` raises `TypeError` without it. It must be an `async def`. Your `confirm` replaces the default for every member, including navigation and clicks, so return `True` for the routine ones.
- **`run_script` runs with the page's own cookies and sessions.** Use a browser profile that isn't signed in to accounts you wouldn't hand the model.
- **Files move through grants.** Tell the model which grant ids it may use (in your instructions); your `resolve_grant` turns an id into a file or refuses it with `None`. Grants are single use. For downloads, pass `downloads=DownloadOptions(resolve_grant=...)` returning a `DownloadGrant`; files land in a quarantine directory and reach your disk only through the grant's `deliver` callback (local browsers only).
- **`read_diagnostics`** turns on the console and network buffers and drops entries from origins the domain policy refuses.

## Use in your own project

Add the dependencies to your uv project:

```bash
uv add 'openai>=3.31.0' stagehand-openai-sdk
```

The distribution name uses hyphens (`stagehand-openai-sdk`), but the Python import uses underscores (`stagehand_openai_sdk`).

## Troubleshooting

| Symptom | What to check |
| --- | --- |
| Missing API key | Copy `.env.example` to `.env` and set `OPENAI_API_KEY`. |
| Model access error | Set `OPENAI_MODEL` in `.env` to a model your account can use. |
| Chrome doesn't launch | Install Google Chrome or pass `chrome_path` to `launch`. |
| Navigation is blocked | Check `allowed_domains` and `blocked_domains`. The model sees `blocked: not in allowed domains (<host>)`. |
| Missing module or exports | Run `uv sync` and check that the installed `openai` release provides `openai.lib.browser` and `openai.lib.responses_tool_runner` (3.31.0 or later). |

See the [shared limitations](../README.md#limitations) for domain filtering, dialogs and Browserbase downloads, or return to the [repository overview](../README.md).
