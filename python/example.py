import asyncio
import os

from openai import AsyncOpenAI
from openai.lib.responses_tool_runner import AsyncResponsesToolRunner
from stagehand_openai_sdk import StagehandBrowserDriver, create_browser_toolset


async def main() -> None:
    driver = await StagehandBrowserDriver.launch(
        headless=False,
        allowed_domains=["example.com", "iana.org"],
        webrtc="allow",
    )
    bundle = create_browser_toolset(driver)
    try:
        async with AsyncOpenAI() as client:
            runner = AsyncResponsesToolRunner(browser=bundle.toolset)
            response = await runner.run(
                client,
                {
                    "model": os.environ.get("OPENAI_MODEL", "gpt-5.5"),
                    "store": False,
                    "input": "Open example.com and tell me what the page says",
                },
                max_steps=20,
            )
            print(response.output_text)
    finally:
        await bundle.close()


if __name__ == "__main__":
    asyncio.run(main())
