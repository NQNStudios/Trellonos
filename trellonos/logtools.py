import os

PRIORITY_LOW = 0
PRIORITY_MEDIUM = 1
PRIORITY_HIGH = 2


class LogManager(object):
    """ Manages the program's debug log with respect to nested contexts.
    For example, a loop might be a context, and debug information within
    this context all share a priority level.
    """

    def __init__(self, minimum_priority=PRIORITY_MEDIUM, tab_width=4):
        self._minimum_priority = minimum_priority
        self._tab_width = tab_width

        self._contexts = []
        self._context_priorities = []

    @classmethod
    def from_environment_vars(cls):
        minimum_priority = int(os.environ['TRELLONOS_DEBUG_PRIORITY'])
        tab_width = int(os.environ['TRELLONOS_TAB_WIDTH'])

        return cls(minimum_priority, tab_width)

    def __message(self, text):
        # Retrieve the depth of the debug log (current number of contexts)
        context_depth = len(self._contexts)

        # Add a tab for each level of depth
        message = ''
        for i in range(context_depth):
            for i in range(self._tab_width):
                message += ' '

        # Then print the message
        message += text

        print(message)

    def open_context(self, context_name, priority=PRIORITY_MEDIUM):
        self.__message('Opening debug context: ' + context_name)
        self._contexts.append(context_name)
        self._context_priorities.append(priority)


    def close_context(self):
        context_name = self._contexts.pop()
        self._context_priorities.pop()
        self.__message('Closing debug context: ' + context_name)

    def message(self, text):
        context_depth = len(self._contexts)

        if context_depth == 0:
            raise Exception(
                'Tried to print from DebugManager without a context')

        current_priority = self._context_priorities[context_depth - 1]

        if current_priority >= self._minimum_priority:
            self.__message(text)
