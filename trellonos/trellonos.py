import re

from trellotools import Trello
from githubtools import GithubManager
from pythontools import ScriptManager
import logtools as log
from board import Board


TRELLONOS_REGEX = re.compile('^<.+>$')
OUTPUT_BOARD_NAME = 'Trellonos Output'


class Trellonos(object):
    """ Top-level container of Trello data and core processor """

    def __init__(self, trello, github):
        self._trello = trello
        self._github = github
        self._scriptManager = ScriptManager(self)

        self._boards = {}

        meta_boards = {}
        non_meta_boards = {}

        log.open_context('Trellonos initialization.')

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

        log.close_context()

    @classmethod
    def from_environment_vars(cls):
        trello = Trello.from_environment_vars()
        github = GithubManager.from_environment_vars()
        return cls(trello, github)

    @property
    def boards(self):
        return self._boards

    @property
    def trello(self):
        return self._trello

    @property
    def scriptManager(self):
        return self._scriptManager

    def process(self):
        """ Runs all Trellonos processing of open boards """

        log.open_context('Trellonos processing.')

        # Run each board's processing
        for name in self._boards:
            board = self._boards[name]
            board.process(self, self._github, self._scriptManager)

        # Then fill each board's markup fields
        for name in self._boards:
            board = self._boards[name]
            board.fill_cards_markup(self._scriptManager)

        log.close_context()

    def dump_log(self):
        log.dump(self._trello, self.boards[OUTPUT_BOARD_NAME])
