from app.ai.tools.base import BaseTool
from app.core.exceptions import ToolException


class CalculatorTool(BaseTool):
    name = "calculator"

    description = "用于数学计算"

    async def execute(
        self,
        expression: str,
    ):

        try:
            result = eval(expression)
            return str(result)
        except (SyntaxError, NameError, TypeError, ValueError, ArithmeticError) as e:
            raise ToolException(f"计算失败: {e}") from e

    @property
    def schema(self):

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "数学表达式，例如 1+1",
                        }
                    },
                    "required": ["expression"],
                },
            },
        }
