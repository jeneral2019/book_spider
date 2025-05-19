import logging


class Log:

    def __init__(self, module):
        self.logger = logging.getLogger(module)
        self.logger.setLevel(logging.DEBUG)

        # 控制台输出
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)

        # ===== DEBUG 日志文件 handler =====
        debug_handler = logging.FileHandler('logs/debug.log')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # ===== INFO+ 日志文件 handler（不包括 DEBUG）=====
        info_handler = logging.FileHandler('logs/info.log')
        info_handler.setLevel(logging.INFO)
        info_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # ===== 添加到 logger =====
        self.logger.addHandler(console_handler)
        self.logger.addHandler(debug_handler)
        self.logger.addHandler(info_handler)

    def debug(self, message):
        self.logger.debug(message)

    def info(self, message):
        self.logger.info(message)

    def error(self, message):
        self.logger.error(message)