import asyncio
import sys


def use_selector_event_loop_on_windows() -> None:
    """psycopg 异步在 Windows 上不能用默认的 ProactorEventLoop。"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


use_selector_event_loop_on_windows()
