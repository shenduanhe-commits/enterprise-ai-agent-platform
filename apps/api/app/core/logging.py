import logging


def setup_logging():
    """
    设置日志配置
    """
    logging.basicConfig(
        level=logging.INFO,
        format=("%(asctime)s [%(levelname)s] %(name)s: %(message)s"),
    )


"""
 获取日志记录器
"""
logger = logging.getLogger("eaap")
