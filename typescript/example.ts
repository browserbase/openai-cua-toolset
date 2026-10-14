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
