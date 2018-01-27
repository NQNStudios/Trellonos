import re

from trellotools import Trello
from githubtools import GithubManager
from pythontools import ScriptManager
import pickle
import logtools as log
from board import Board
from os.path import expanduser
home = expanduser("~")

TRELLONOS_REGEX = re.compile('^<.+>$')
OUTPUT_BOARD_NAME = 'Trellonos Output'


class Trellonos(object):
    """ Top-level container of Trello data and core processor """

    def __init__(self, trello, boards_needed=[], github=None):
        self._trello = trello
        self._github = github
        self._script_manager = ScriptManager(self)

        self._boards_needed = boards_needed

        if boards_needed == 'USE_BACKUP':
            with open(home + '/.lasttrellonos', 'r') as f:
                self._boards = pickle.load(f)

            self._boards_needed = []
            # Give them all a live trello object
            for board in self._boards:
                self._boards_needed.append(board)
                self._boards[board].update_trello_instance(trello)
        else:
            self.populate_boards()
            self.serialize_boards()

    @classmethod
    def from_environment_vars(cls):
        trello = Trello.from_environment_vars()
        github = GithubManager.from_environment_vars()
        return cls(trello, github)

    def serialize_boards(self):
        with open(home + '/.lasttrellonos', 'w+') as f:
            pickle.dump(self._boards, f)

    def populate_boards(self):
        trello = self._trello
        github = self._github
        boards_needed = self._boards_needed

        self._boards = {}

        meta_boards = {}
        non_meta_boards = {}

        log.open_context('Trellonos board population.')

        # Iterate and initialize board objects from subscribed Trello boards
        for trello_board in trello.get_boards():
            board_name = trello_board['name']

            # If boards_needed is empty, take all boards. Otherwise,
            # don't

            # Look for metaboards to find subscribed boards
            if re.search(TRELLONOS_REGEX, board_name):
                # Strip board name of tags before mapping
                board_key = board_name[1:-1]

                if board_key in boards_needed or len(boards_needed) == 0:
                    meta_boards[board_key] = trello_board
            else:
                if board_name in boards_needed or len(boards_needed) == 0:
                    non_meta_boards[board_name] = trello_board


        # first construct processor-enabled board objects from normal boards
        # and meta counterparts as long as a Github object is provided to
        # process them
        if github != None:
            for board_name in meta_boards:
                normal_board = non_meta_boards[board_name]
                meta_board = meta_boards[board_name]

                board_object = Board(trello, normal_board, meta_board)

                self._boards[board_name] = board_object

        # Then construct non-processing boards from leftover normal boards
        for board_name in non_meta_boards:
            if board_name not in self._boards:
                board_object = Board(trello, non_meta_boards[board_name])

                self._boards[board_name] = board_object

        log.close_context()



    @property
    def boards(self):
        return self._boards

    @property
    def trello(self):
        return self._trello

    @property
    def script_manager(self):
        return self._script_manager

    def process(self):
        """ Runs all Trellonos processing of open boards """

        if not self._github:
            log.message("Can't run Trellonos processing without a Github account")

        log.open_context('Trellonos processing.')

        # Run each board's processing
        for name in self._boards:
            board = self._boards[name]
            board.process(self, self._github, self._script_manager)

        # Then fill each board's markup fields
        for name in self._boards:
            board = self._boards[name]
            board.fill_cards_markup(self._script_manager)

        log.close_context()

    def dump_log(self):
        log.dump(self._trello, self.boards[OUTPUT_BOARD_NAME])
