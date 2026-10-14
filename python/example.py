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
