#! /usr/bin/env python

from trellotools import Trello
from githubtools import GithubManager
from trellonos import Trellonos

# Construct a Trellonos object using environment variable settings
trello = Trello.from_environment_vars()
github = GithubManager.from_environment_vars()
trellonos = Trellonos(trello, github)

board = trellonos.boards['Planner']
tlist = board.lists['Monday May 04']
tcard = tlist.cards[0]
tcard.copy(trello)
