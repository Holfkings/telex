// @ts-nocheck
import OpenAI from "openai";

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function askQuestion(prompt: string) {
  const res = await openai.completions.create({
    model: "gpt-3.5-turbo-instruct",
    prompt: prompt,
  });
  return res.choices[0].text;
}
