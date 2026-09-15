// @ts-nocheck
import { Configuration, OpenAIApi } from "openai";

const configuration = new Configuration({ apiKey: process.env.OPENAI_API_KEY });
const openai = new OpenAIApi(configuration);

export async function askQuestion(prompt: string) {
  const res = await openai.createCompletion({
    model: "text-davinci-003",
    prompt: prompt,
  });
  return res.data.choices[0].text;
}
