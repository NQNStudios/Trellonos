import os
import datetime

PRIORITY_LOW = 0
PRIORITY_MEDIUM = 1
PRIORITY_HIGH = 2


# This module manages the program's debug log with respect to nested
# contexts. For example, a loop might be a context, and debug
# information within this context all share a priority level.

_minimum_priority = PRIORITY_MEDIUM
_tab_width = 4


_contexts = []
_context_priorities = []
_text = ''

def init_from_environment_vars():
    global _minimum_priority
    global _tab_width
    _minimum_priority = int(os.environ['TRELLONOS_DEBUG_PRIORITY'])
    _tab_width = int(os.environ['TRELLONOS_TAB_WIDTH'])

def _context_depth():
    return len(_contexts)

def _current_priority():
    if _context_depth() == 0:
        return PRIORITY_MEDIUM

    return _context_priorities[_context_depth() - 1]

def _print(line):
    global _text
    # Print the line
    _text += line + '\n'
    # Also save it in the log's text for dumping
    print(line)

def _message(text):
    # Add a tab for each level of depth
    message = ''
    for i in range(_context_depth()):
        for i in range(_tab_width):
            message += ' '

    # Then print the message
    message += str(text)

    _print(message)

def open_context(context_name, priority=None):
    if not priority:
        priority = _current_priority

    # Announce the opening if priority warrants
    message('Opening debug context: ' + context_name)

    # Add the priority to the end of the list
    # But if the current context is lower priority, keep the current
    _context_priorities.append(min(_current_priority, priority))

    # Add the name to the end of the list
    # It is important that this call comes second!
    _contexts.append(context_name)

def close_context():
    # Retrieve the name of the current context, removing it from the list
    context_name = _contexts.pop()

    # Remove the current priority from the end of the list
    _context_priorities.pop()

    # Annouce the removal of the context
    _message('Closing debug context: ' + context_name)

def message(text):
    if _current_priority >= _minimum_priority:
        _message(text)

# Dump all previous output into a card in the given board
def dump(trello, board):
    global _text

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
    output = '```\n' + _text + '```\n'
    output_card.set_description(trello, output)
    # Clear text stored in the log
    _text = ''
