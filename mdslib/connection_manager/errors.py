class NXOSError(Exception):
    """

    """

    def __init__(self, message):
        """

        Args:
            message:
        """
        self.message = message.strip()

    def __repr__(self):
        """

        Returns:

        """
        return '%s: %s' % (self.__class__.__name__, self.message)

    __str__ = __repr__


class CLIError(NXOSError):
    """

    """

    def __init__(self, command, message):
        """

        Args:
            command:
            message:
        """
        self.command = command.strip()
        self.message = message.strip()

    def __repr__(self):
        """

        Returns:

        """
        return 'The command " %s " gave the error " %s ".' % (self.command, self.message)

    __str__ = __repr__
