from abc import ABC, abstractmethod

class BaseBackend(ABC):
    @abstractmethod
    def complete(self, system: str, user: str) -> str: ...
