from app.ai.tools.base import BaseTool


class SendEmailTool(BaseTool):
    name = "send_email"
    description = "发送邮件。调用后必须经人工批准才会发送。"
    requires_approval = True

    async def execute(self, to: str, subject: str = "", body: str = ""):
        return f"已发送 to={to} subject={subject}"

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
                        "to": {"type": "string", "description": "收件人邮箱"},
                        "subject": {"type": "string", "description": "主题"},
                        "body": {"type": "string", "description": "正文"},
                    },
                    "required": ["to"],
                },
            },
        }
