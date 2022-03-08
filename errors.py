class EmptyBufferError(Exception):
    """
    Raised when the buffer returns as NoneType.
    """

    default_msg = 'The buffer seems to be empty, is your device transmitting?'

    def __init__(self, message: str = default_msg):
        """

        Instantiate the exception.

        Arguments:

            message (str):
                Include additional information that may help the end-user or developers figure out why the buffer is
                empty.
        """

        if message != self.default_msg:
            msg = self.default_msg + f"\n\nSome more information from the caller: {message}"
            message = msg

        Exception.__init__(self, message)


class PortInUseError(Exception):
    """
    Raised when an attempt to connect to the socket fails due to the port already being in-use.
    """

    default_msg = "Illegal port-binding attempt. Port in use!"

    def __init__(self, message=default_msg):
        if message != self.default_msg:
            msg = self.default_msg + f"\n\nSome more information from the caller: {message}"
            message = msg

        Exception.__init__(self, message)

