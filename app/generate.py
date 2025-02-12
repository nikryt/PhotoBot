from openai import AsyncOpenAI
from config import AI_TOKEN, DS_TOKEN

client = AsyncOpenAI(
  base_url="https://openrouter.ai/api/v1",
  # base_url="https://api.deepseek.com",
  api_key=AI_TOKEN,
  # api_key=DS_TOKEN
)

async def ai_generate(text: str):
  completion = await client.chat.completions.create(

    model="deepseek/deepseek-chat:free",
    messages=[
      {
        "role": "user",
        "content": text
      }
    ]
  )
  print(completion)
  return completion.choices[0].message.content