import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url=os.environ.get("LLM_BASE_URL", "https://openrouter.ai/api/v1"), 
    api_key=os.environ.get("LLM_API_KEY")
)

res = client.chat.completions.create(
    model=os.environ.get("LLM_MODEL", "openrouter/free"),
    messages=[{"role": "user", "content": "Reply with exactly the word: ready"}],
)

print(res.choices[0].message.content)
