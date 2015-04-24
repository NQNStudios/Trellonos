import re

from list import List


METADATA_REGEX = re.compile('^<.+>$')
SPECIAL_META_LISTS = {
    'Archetypes': '__archetypes',
    'Board Processors': '__board_processors',
    'List Processors': '__list_processors',
    'List Defaults': '__list_defaults',
    'Card Processors': '__card_processors'
}


def execute_processor(github, processor, input):
    yaml_data = processor.yaml_data

    gist_id = yaml_data['gist_id']
    gist_file = yaml_data['gist_file']

    github.execute_gist(gist_id, gist_file, input)


class Board(object):
    """ Wrapper of a Trello board """

    def __init__(self, trello, trello_board, meta_board):
        self.__trello = trello
        self.__board_data = trello_board
        self.__meta_board = meta_board

        self.__lists = {}
        self.__closed_lists = {}

        self.__meta_lists = {}

        self.__archetypes = {}
        self.__board_processors = {}
        self.__list_processors = {}
        self.__card_processors = {}
        self.__list_defaults = {}

        # retrieve lists in the board
        trello_lists = trello.get_lists(trello_board)
        meta_lists = trello.get_lists(meta_board)

        # First retrieve meta lists
        for meta_list in meta_lists:
            list_name = meta_list['name']

            meta_list_object = List(trello, meta_list)

            # handle special meta lists
            if meta_list_object.open and re.search(METADATA_REGEX, list_name):
                # strip <meta tags>
                list_name = list_name[1:-1]

                # TODO make this clean with setattr() or exec()
                if list_name == "Archetypes":
                    self.__archetypes = meta_list_object
                elif list_name == "Board Processors":
                    self.__board_processors = meta_list_object
                elif list_name == "List Processors":
                    self.__list_processors = meta_list_object
                elif list_name == "List Defaults":
                    self.__list_defaults = meta_list_object
                elif list_name == "Card Processors":
                    self.__card_processors = meta_list_object


            # handle regular meta lists
            elif meta_list_object.open:
                # map the list
                self.__meta_lists[list_name] = meta_list_object

            # closed meta lists will be discarded altogether!

        # map lists in a dictionary by name
        for trello_list in trello_lists:
            list_name = trello_list['name']

            list_object = List(trello, trello_list)

            # if archetypes are defined, apply them to this list
            if self.__archetypes:
                list_object.apply_archetypes(self.__archetypes)

            # map the list by name
            if list_object.open:
                self.__lists[list_name] = list_object
            else:
                self.__closed_lists[list_name] = list_object

    @property
    def num_list_processors(self):
        return len(self.__list_processors.cards)

    @property
    def name(self):
        return self.__board_data['name']

    @property
    def open(self):
        return not self.__board_data['closed']

    @property
    def closed(self):
        return self.__board_data['closed']

    def archive(self, trello):
        self.__board_data['closed'] = True
        trello.update_board_closed(self.__board_data, True)

    def unarchive(self, trello):
        self.__board_data['closed'] = False
        trello.update_board_closed(self.__board_data, False)

    @property
    def lists(self):
        return self.__lists

    @property
    def closed_lists(self):
        return self.__closed_lists

    @property
    def meta_lists(self):
        return self.__meta_lists

    def create_list(self, name):
        """ Creates a list in this board but does not add it to Trellonos """

        trello_list = self.__trello.create_list(self.__board_data, name)

        self.__lists[name] = List(self.__trello, trello_list)

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
        """ Run each of this board's many types of processors """

        # first, processors of the whole board
        for board_processor in self.__board_processors:
            print("running board processor " + board_processor.name)

            # send the board as an argument, and trello wrapper
            input_dict = {'board': self, 'trello': self.__trello}

            # execute the board processor
            execute_processor(github, board_processor, input_dict)
            print("done running board processor " + board_processor.name)

        # Then list processors
        for list_processor in self.__list_processors:
            list_name = list_processor.name
            print("running list processor " + list_name)

            input_list = self.__lists[list_name]

            # Pass the list with the same name as an argument
            input_dict = {'list': input_list, 'trello': self.__trello}
            execute_processor(github, list_processor, input_dict)
            print("done running list processor " + list_name)

        # Then card processors
        for card_processor in self.__card_processors:
            type_name = card_processor.name
            print("running card processor " + type_name)

            # process all cards of the given type name individually
            cards = self.get_cards(type_name)

            for card in cards:
                input_dict = {'card': card, 'trello': self.__trello}
                execute_processor(github, card_processor, input_dict)

            print("done running card processor " + type_name)
