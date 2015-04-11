import re

from board import Board


TRELLONOS_REGEX = re.compile('^<.+>$')


class Trellonos(object):

    def __init__(self, trello, github):
        self.__trello = trello
        self.__github = github

        self.__boards = {}
        self.__closed_boards = {}

        # Iterate and initialize board objects from subscribed Trello boards
        for trello_board in trello.get_boards():
            board_name = trello_board['name']

            # Only pay attention to boards marked with names in <>
            if re.search(TRELLONOS_REGEX, board_name):
                # Strip board name of tags before mapping
                board_key = board_name[1:-1]

                # Construct the Trellonos board object
                board = Board(trello, trello_board)

                # Separate open and closed boards in 2 maps
                if board.open:
                    self.__boards[board_key] = board
                else:
                    self.__closed_boards[board_key] = board

    @property
    def boards(self):
        return self.__boards

    @property
    def closed_boards(self):
        return self.__closed_boards

    def process(self):
        """ Runs all Trellonos processing of open boards """
        for board_key in self.__boards:
            # Run each board's processing
            board = self.__boards[board_key]

            board.process(self.__github)
