# shared_logger.py
import logging
import datetime



def setup_logger(logfile):
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)  # 设置日志记录器的级别为DEBUG

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(logfile)
        file_handler.setLevel(logging.DEBUG)  # 设置文件处理器的级别为DEBUG
        file_handler.setFormatter(formatter)

        logger.addHandler(file_handler)

        # 添加控制台处理器，将日志消息输出到控制台
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)  # 设置控制台处理器的日志级别为INFO
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
