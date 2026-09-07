from openai import AsyncOpenAI
from .base import BaseLLMProvider
from ..config import settings
class OpenAIProvider(BaseLLMProvider):
 async def complete(self, system, message):
  if not settings.openai_api_key: raise RuntimeError("OPENAI_API_KEY is not configured")
  c=AsyncOpenAI(api_key=settings.openai_api_key)
  r=await c.chat.completions.create(model=settings.openai_model,messages=[{"role":"system","content":system},{"role":"user","content":message}],temperature=.2)
  return r.choices[0].message.content or ""
def provider_for(name):
 return OpenAIProvider() if name=="openai" else __import__("app.providers.ollama_provider",fromlist=["OllamaProvider"]).OllamaProvider()
