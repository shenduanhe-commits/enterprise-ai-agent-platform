from abc import ABC, abstractmethod


class BaseTool(ABC):
    name: str

    description: str

    requires_approval: bool = False

    @abstractmethod
    async def execute(
        self,
        **kwargs,
    ):
        pass

    @property
    def schema(self) -> dict:

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": [],
                },
            },
        }
