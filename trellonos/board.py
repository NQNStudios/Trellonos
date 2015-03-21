import re

from list import List


METADATA_REGEX = re.compile('^<.+>$')


class Board(object):

    def __init__(self, trello, trello_board):
        self.__board_data = trello_board

        self.__lists = {}

        trello_lists = trello.get_lists(trello_board)

        for trello_list in trello_lists:
            list_name = trello_list['name']

            list_object = List(trello, trello_list)

            if re.search(METADATA_REGEX, list_name):
                list_name = list_name[1:-1]

                if list_name == 'Archetypes':
                    self.__archetypes = list_object
                elif list_name == 'Processors':
                    self.__processors = list_object
            else:
                if self.__archetypes:
                    list_object.apply_archetypes(self.__archetypes)

                self.__lists[list_name] = list_object

    @property
    def lists(self):
        return self.__lists

    def get_cards(type_name):
        cards = []

        for tlist in self.__lists:
            for card in tlist:
                if type_name == '<All>' or card.type_name == type_name:
                    cards.append(card)

        return cards

    def process(self):
        for processor in self.__processors:
            type_name = processor.name

            yaml_data = processor.yaml_data

        # TODO finish this function
