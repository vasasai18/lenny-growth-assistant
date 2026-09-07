from abc import ABC, abstractmethod
class BaseLLMProvider(ABC):
    @abstractmethod
    async def complete(self, system: str, message: str) -> str: ...
