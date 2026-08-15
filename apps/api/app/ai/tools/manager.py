from app.ai.tools.base import BaseTool


class ToolManager:
    def __init__(self):

        self.tools: dict[str, BaseTool] = {}

    def register(
        self,
        tool: BaseTool,
    ):

        self.tools[tool.name] = tool

    def get(
        self,
        name: str,
    ) -> BaseTool | None:

        return self.tools.get(name)

    def list_tools(
        self,
    ) -> list[BaseTool]:

        return list(self.tools.values())

    def get_schemas(
        self,
    ) -> list[dict]:

        return [tool.schema for tool in self.tools.values()]
