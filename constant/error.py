class Interrupt(Exception):
    pass


class QQAPIError(Exception):
    pass


class ErrorWithMsg(Exception):
    def __init__(self, msg):
        self.msg = msg


class SecCheckError(ErrorWithMsg):
    pass


class TooFast(ErrorWithMsg):
    pass


class DiceError(ErrorWithMsg):
    pass


class ExpressionError(DiceError):
    pass


class ExpressionUnresolvedError(ExpressionError):
    pass


class ExpressionLimitError(ExpressionError):
    pass


class ExpressionFormatError(ExpressionError):
    pass
