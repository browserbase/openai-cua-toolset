import OpenAI from "openai";
import { ResponsesToolRunner } from "openai/helpers/responses-tool-runner";
import {
  StagehandBrowserDriver,
  createBrowserToolset,
} from "stagehand-openai-sdk";

const driver = await StagehandBrowserDriver.launch({
  headless: false,
  allowedDomains: ["example.com", "iana.org"],
});
const browser = createBrowserToolset(driver);

try {
  const runner = new ResponsesToolRunner({ browser });
  const response = await runner.run(
    new OpenAI(),
    {
      model: process.env.OPENAI_MODEL ?? "gpt-6-luna",
      store: false,
      input: "Open example.com and tell me what the page says",
    },
    { maxSteps: 20 },
  );
  console.log(response.output_text);
} finally {
  await driver.close();
}
