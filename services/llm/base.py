from abc import ABC, abstractmethod
from typing import Any


class BaseLLMService(ABC):
    @abstractmethod
    async def complete(self, system: str, user: str, max_tokens: int = 2048) -> str:
        ...

    @abstractmethod
    async def complete_json(self, system: str, user: str, max_tokens: int = 2048) -> Any:
        ...
