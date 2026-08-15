class EAAPException(Exception):
    """
    EAAP基础业务异常
    """

    def __init__(self, status_code: int, message: str, code: int):
        self.status_code = status_code
        self.message = message
        self.code = code

        super().__init__(self.message)


class NotFoundException(EAAPException):
    def __init__(self, message: str = "Resource not found", code: int = 404):

        super().__init__(404, message, code)


class BusinessException(EAAPException):
    def __init__(self, message: str = "Business error", code: int = 400):

        super().__init__(400, message, code)


class AgentRuntimeException(EAAPException):
    def __init__(self, message: str = "Agent runtime error", code: int = 500):
        super().__init__(500, message, code)


class LLMException(AgentRuntimeException):
    def __init__(self, message: str = "LLM error", code: int = 500):
        super().__init__(message, code)


class PromptException(AgentRuntimeException):
    def __init__(self, message: str = "Prompt error", code: int = 500):
        super().__init__(message, code)


class MemoryException(AgentRuntimeException):
    def __init__(self, message: str = "Memory error", code: int = 500):
        super().__init__(message, code)


class ToolException(AgentRuntimeException):
    def __init__(self, message: str = "Tool error", code: int = 500):
        super().__init__(message, code)
