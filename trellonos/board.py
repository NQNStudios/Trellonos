import re

from list import List


METADATA_REGEX = re.compile('^<.+>$')


class Board(object):
    """ Wrapper of a Trello board """

    def __init__(self, trello, trello_board):
        self.__trello = trello
        self.__board_data = trello_board

        self.__lists = {}
        self.__closed_lists = {}
        self.__archetypes = {}
        self.__processors = {}

        # retrieve lists in the board
        trello_lists = trello.get_lists(trello_board)

        # map lists in a dictionary by name
        for trello_list in trello_lists:
            list_name = trello_list['name']

            list_object = List(trello, trello_list)

            # handle meta lists specially
            if list_object.open and re.search(METADATA_REGEX, list_name):
                # stip <meta tags>
                list_name = list_name[1:-1]

                if list_name == 'Archetypes':
                    self.__archetypes = list_object
                elif list_name == 'Processors':
                    self.__processors = list_object
            # handle regular lists
            else:
                # map the list
                if list_object.open:
                    self.__lists[list_name] = list_object
                else:
                    self.__closed_lists[list_name] = list_object

        if self.__archetypes:
            # Apply archetypes to every list
            for list_key, list_object in self.__lists.iteritems():
                list_object.apply_archetypes(self.__archetypes)

            # Then to every closed list, for good measure
            for list_key, list_object in self.__closed_lists.iteritems():
                list_object.apply_archetypes(self.__archetypes)

    @property
    def name(self):
        return self.__board_data['name']

    @property
    def open(self):
        return not self.__board_data['closed']

    @property
    def closed(self):
        return self.__board_data['closed']

    @property
    def lists(self):
        return self.__lists

    @property
    def closed_lists(self):
        return self.__closed_lists

    def get_cards(self, type_name):
        """ Retrieve the cards from this board given a type name """
        cards = []

        # Iterate through lists
        for list_key in self.__lists:
            tlist = self.__lists[list_key]

            # For each list, iterate through cards
            for card in tlist:
                # Add the card if it matches OR if we want all cards
                if type_name == '<All>' or card.type_name == type_name:
                    cards.append(card)

        return cards

    def process(self, github):
        """ Run each processor on its corresponding cards """
        for processor in self.__processors:
            type_name = processor.name

            yaml_data = processor.yaml_data

            # Retrieve the processor gist
            gist_id = yaml_data['gist_id']
            gist_file = yaml_data['gist_file']

            # Some processors process the entire board, no specific card type
            if type_name == '<None>':
                input_dict = {'board': self, 'trello': self.__trello}
                github.execute_gist(gist_id, gist_file, input_dict)
            # The rest will process individual cards
            else:
                for card in self.get_cards(type_name):
                    input_dict = {'card': card, 'trello': self.__trello}
                    github.execute_gist(gist_id, gist_file, input_dict)
