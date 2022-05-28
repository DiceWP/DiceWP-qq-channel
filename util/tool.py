from timeit import default_timer

from qqbot.core.util.logging import getLogger

logger = getLogger("bot")

class TimeRecorder:
    def __init__(self, log_label="总用时"):
        """
        :param log_label:  自定义log的文字
        """
        self._start = default_timer()
        self._log_label = log_label

    def __enter__(self):
        self.start()

    def __exit__(self, *exc_info):
        self.rec()

    def start(self):
        self._start = default_timer()

    def rec(self):
        diff = default_timer() - self._start
        logger.debug("-- %s: %.6f 秒" % (self._log_label, diff))
