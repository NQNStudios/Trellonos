import re

from list import List


METADATA_REGEX = re.compile('^<.+>$')

# Single underscore attributes to avoid mangling-related error
# Because these fields will be set dynamically (hence the dictionary)
SPECIAL_META_LISTS = {
    'Archetypes': '_archetypes',
    'Board Processors': '_board_processors',
    'List Processors': '_list_processors',
    'List Defaults': '_list_defaults',
    'Card Processors': '_card_processors'
}


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

            meta_list_object = List(trello, self, meta_list)

            # handle special meta lists
            if re.search(METADATA_REGEX, list_name):
                list_name = list_name[1:-1]

                if list_name in SPECIAL_META_LISTS:
                    # If it's a special meta list, save it as an attribute
                    # Because it shouldn't be outwardly accessible
                    attribute_name = SPECIAL_META_LISTS[list_name]
                    self.__dict__[attribute_name] = meta_list_object

            # handle regular meta lists
            elif meta_list_object.open:
                # map the list
                self.__meta_lists[list_name] = meta_list_object

            # closed meta lists will be discarded altogether!

        # map lists in a dictionary by name
        for trello_list in trello_lists:
            list_name = trello_list['name']

            list_object = List(trello, self, trello_list)

            # if archetypes are defined, apply them to this list
            if self._archetypes:
                list_object.apply_archetypes(self._archetypes)

            # map the list by name
            if list_object.open:
                self.__lists[list_name] = list_object
            else:
                self.__closed_lists[list_name] = list_object

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
        """ Creates a list in this board. Adds the list to this
        board's dictionary and returns the Trellonos wrapper object """

        trello_list = self.__trello.create_list(self.__board_data, name)

        new_list = List(self.__trello, self, trello_list)
        self.__lists[name] = new_list

        return new_list

    def sort_list(self, list_object, position):
        """ Sorts the given list (supplied as Trellonos  wrapper) to the given
        position. Position can be 'top', 'bottom', or a positive number """

        list_object.sort(self.__trello, position)

    def sort_list_between(self, list_object, list_a, list_b):
        """ Sorts the given list (supplied as Trellonos wrapper) to a
        position between the two other given lists.

        If list_ a or list_b is None, list_object will be sorted to the
        position immediately adjacent the existing list, i.e. "between"
        the existing list and nothing on the empty side. """
        left_bound = None
        right_bound = None
        new_position = None

        if list_a:
            left_bound = list_a.position
        elif list_b:
            # left bound doesn't exist, move left of the right bound
            new_position = list_b.position - 1

        if list_b:
            right_bound = list_b.position
        elif list_a:
            # right bound doesn't exist, move right of the left bound
            new_position = list_a.position + 1

        if left_bound and right_bound:
            # Average the position of two existing bound lists
            new_position = (left_bound + right_bound) / 2

        if new_position:
            self.sort_list(list_object, new_position)
        else:
            raise ValueError('Tried to sort list between two \
                             non-existent lists')

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

    def execute_processor(self, github, processor, input):
        """ Executes a board/list/card processor using the yaml data in the
        card which defines it """

        yaml_data = processor.yaml_data

        gist_id = yaml_data['gist_id']
        gist_file = yaml_data['gist_file']

        # Pass all yaml data as input, including gist_id and gist_file
        # Although they will rarely be used, there's no harm in it
        for field in yaml_data:
            if field not in input:  # of course, avoid overwrite error
                input[field] = yaml_data[field]

        # Pass the GithubManager into the processor as input
        input['github'] = github

        # Return the output dictionary
        return github.execute_gist(gist_id, gist_file, input)

    def process(self, github):
        """ Run each of this board's many types of processors """

        # first, processors of the whole board
        for board_processor in self._board_processors:
            print("running board processor " + board_processor.name)

            # send the board as an argument, and trello wrapper
            input_dict = {'board': self, 'trello': self.__trello}

            # execute the board processor
            self.execute_processor(github, board_processor, input_dict)
            print("done running board processor " + board_processor.name)

        # Then list processors
        for list_processor in self._list_processors:
            list_name = list_processor.name
            print("running list processor " + list_name)

            input_list = self.__lists[list_name]

            # Pass the list with the same name as an argument
            input_dict = {'list': input_list, 'trello': self.__trello}
            self.execute_processor(github, list_processor, input_dict)
            print("done running list processor " + list_name)

        # Then card processors
        for card_processor in self._card_processors:
            type_name = card_processor.name
            print("running card processor " + type_name)

            # process all cards of the given type name individually
            cards = self.get_cards(type_name)

            for card in cards:
                input_dict = {'card': card, 'trello': self.__trello}
                self.execute_processor(github, card_processor, input_dict)

            print("done running card processor " + type_name)
