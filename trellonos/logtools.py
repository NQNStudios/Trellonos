import os
import datetime

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
        self._text = ''

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

    def _print(self, line):
        # Print the line
        self._text += line + '\n'
        # Also save it in the log's text for dumping
        print(line)

    def _message(self, text):
        # Add a tab for each level of depth
        message = ''
        for i in range(self._context_depth):
            for i in range(self._tab_width):
                message += ' '

        # Then print the message
        message += str(text)

        self._print(message)

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

    # Dump all previous output into a card in the given board
    def dump(self, trello, board):
        # Get the date and time
        time = datetime.datetime.now()
        # Place the new output card in a list for the current month
        list_name = time.strftime('%B %Y')
        # Create the list if it doesn't exist yet
        if list_name not in board.lists.keys():
            board.create_list(list_name)
        # Get the list
        month_list = board.lists[list_name]
        # Create a card for this session
        card_name = time.strftime('%c')
        output_card = month_list.create_card(trello, card_name)
        # Dump all output into the output card
        output = '```\n' + self._text + '```\n'
        output_card.set_description(trello, output)
        # Clear text stored in the log
        self._text = ''
