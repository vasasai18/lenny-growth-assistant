import httpx
from .base import BaseLLMProvider
from ..config import settings
class OllamaProvider(BaseLLMProvider):
 async def complete(self, system, message):
  async with httpx.AsyncClient(timeout=60) as c:
   r=await c.post(f"{settings.ollama_base_url}/api/chat",json={"model":settings.ollama_model,"stream":False,"messages":[{"role":"system","content":system},{"role":"user","content":message}]})
   r.raise_for_status(); return r.json()["message"]["content"]
