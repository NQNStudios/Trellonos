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

    @property
    def _context_depth(self):
        return len(self._contexts)

    @property
    def _current_priority(self):
        if self._context_depth == 0:
            return PRIORITY_MEDIUM

        return self._context_priorities[self._context_depth - 1]

    def _message(self, text):
        # Add a tab for each level of depth
        message = ''
        for i in range(self._context_depth):
            for i in range(self._tab_width):
                message += ' '

        # Then print the message
        message += text

        print(message)

    def open_context(self, context_name, priority=None):
        if not priority:
            priority = self._current_priority

        # Announce the opening if priority warrants
        self.message('Opening debug context: ' + context_name)

        # Add the priority to the end of the list
        # But if the current context is lower priority, keep the current
        self._context_priorities.append(min(self._current_priority, priority))

        # Add the name to the end of the list
        # It is important that this call comes second!
        self._contexts.append(context_name)

    def close_context(self):
        # Retrieve the name of the current context, removing it from the list
        context_name = self._contexts.pop()

        # Remove the current priority from the end of the list
        self._context_priorities.pop()

        # Annouce the removal of the context
        self._message('Closing debug context: ' + context_name)

    def message(self, text):
        if self._current_priority >= self._minimum_priority:
            self._message(text)
