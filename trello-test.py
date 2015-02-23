#! /usr/bin/env python

from trellotools import Trello
from pprint import PrettyPrinter

trello = Trello("80779dd2f1f177a070b745af73f1aa8f", "7bf40878369f0013db8530360cf95daeae1d9580f46c4ef561c443c9592f2af8")

planner = trello.get_board("Planner")
print(planner)
today = trello.get_lists_with_keyword(planner, 'Sunday')[0]
print(today)
cards = trello.get_cards(today)
print(cards)
card = cards[0]
pp = PrettyPrinter()
pp.pprint(card)
