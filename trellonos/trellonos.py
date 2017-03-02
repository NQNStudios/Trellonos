import re

from trellotools import Trello
from githubtools import GithubManager
from logtools import LogManager
from board import Board


TRELLONOS_REGEX = re.compile('^<.+>$')
OUTPUT_BOARD_NAME = 'Trellonos Output'


class Trellonos(object):
    """ Top-level container of Trello data and core processor """

    def __init__(self, trello, github, log):
        self._trello = trello
        self._github = github
        self._log = log

        self._boards = {}

        meta_boards = {}
        non_meta_boards = {}

        self._log.open_context('Trellonos initialization.')

        # Iterate and initialize board objects from subscribed Trello boards
        for trello_board in trello.get_boards():
            board_name = trello_board['name']

            # Look for metaboards to find subscribed boards
            if re.search(TRELLONOS_REGEX, board_name):
                # Strip board name of tags before mapping
                board_key = board_name[1:-1]

                meta_boards[board_key] = trello_board
            else:
                non_meta_boards[board_name] = trello_board

        # next construct board objects from normal boards and meta counterparts
        for board_name in meta_boards:
            normal_board = non_meta_boards[board_name]
            meta_board = meta_boards[board_name]

            board_object = Board(log, trello, normal_board, meta_board)

            self._boards[board_name] = board_object

        self._log.close_context()

    @classmethod
    def from_environment_vars(cls):
        trello = Trello.from_environment_vars()
        github = GithubManager.from_environment_vars()
        log = LogManager.from_environment_vars()
        return cls(trello, github, log)

    @property
    def boards(self):
        return self._boards

    def process(self):
        """ Runs all Trellonos processing of open boards """

        self._log.open_context('Trellonos processing.')

        for board_key in self._boards:
            # Run each board's processing
            board = self._boards[board_key]

            board.process(self._github)

        self._log.close_context()

    def dump_log(self):
        self._log.dump(self._trello, self.boards[OUTPUT_BOARD_NAME])
