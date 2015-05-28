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

    def __init__(self, log, trello, trello_board, meta_board):
        self.__log = log
        self.__trello = trello
        self._board_data = trello_board
        self.__meta_board = meta_board

        self._lists = {}

        self.__meta_lists = {}

        # Set special meta lists to empty before they are found
        for list_name in SPECIAL_META_LISTS:
            setattr(self, SPECIAL_META_LISTS[list_name], {})

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
            else:
                # map the list
                self.__meta_lists[list_name] = meta_list_object

            # closed meta lists will be discarded altogether by API filter

        # map regular lists in a dictionary by name
        for trello_list in trello_lists:
            list_name = trello_list['name']

            list_object = List(trello, self, trello_list)

            # if this list has a default type name, apply it
            if self._list_defaults:
                # Find the default card
                default_card = self._list_defaults.get_card(list_name)

                # Only apply a default if it exists
                if default_card:
                    type_name = default_card.type_name
                    list_object.apply_default_type(type_name)

            # if archetypes are defined, apply them to this list
            if self._archetypes:
                list_object.apply_archetypes(self._archetypes)

            # map the list by name
            self._lists[list_name] = list_object

    @property
    def name(self):
        return self._board_data['name']

    @property
    def open(self):
        return not self._board_data['closed']

    @property
    def closed(self):
        return self._board_data['closed']

    def archive(self, trello):
        self._board_data['closed'] = True
        trello.update_board_closed(self._board_data, True)

    def unarchive(self, trello):
        self._board_data['closed'] = False
        trello.update_board_closed(self._board_data, False)

    @property
    def lists(self):
        return self._lists

    @property
    def meta_lists(self):
        return self.__meta_lists

    def create_list(self, name):
        """ Creates a list in this board. Adds the list to this
        board's dictionary and returns the Trellonos wrapper object """

        trello_list = self.__trello.create_list(self._board_data, name)

        new_list = List(self.__trello, self, trello_list)
        self._lists[name] = new_list

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
            raise ValueError(
                'Tried to sort list between two non-existent lists')

    def get_cards(self, type_name):
        """ Retrieve the cards from this board given a type name """
        cards = []

        # Iterate through lists
        for list_key in self._lists:
            tlist = self._lists[list_key]

            # For each list, iterate through cards
            for card in tlist:
                # Add the card if it matches OR if we want all cards
                if type_name == '<All>' or card.type_name == type_name:
                    cards.append(card)

        return cards

    def is_processor(self, processor):
        """ Tests whether a card is a processor """
        if 'gist_id' not in processor.yaml_data:
            return False

        if 'gist_file' not in processor.yaml_data:
            return False

        return True

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

        # Pass the LogManager as input
        input['log'] = self.__log

        # Pass the Trello wrapper into the processor
        input['trello'] = self.__trello

        # Pass the GithubManager into the processor as input
        input['github'] = github

        # Return the output dictionary
        return github.execute_gist(gist_id, gist_file, input)

    def process(self, github):
        """ Run each of this board's many types of processors """
        self.__log.open_context('Processing board ' + self.name)

        # first, processors of the whole board
        for board_processor in self._board_processors:
            if not self.is_processor(board_processor):
                self.__log.message('Skipping a non-processor')
                continue

            # send the board as an argument, and trello wrapper
            input_dict = {'board': self}

            # execute the board processor
            self.execute_processor(github, board_processor, input_dict)

        # Then list processors
        for list_processor in self._list_processors:
            if not self.is_processor(list_processor):
                continue

            list_name = list_processor.name
            input_list = self._lists[list_name]

            # Pass the list with the same name as an argument
            input_dict = {'list': input_list}
            self.execute_processor(github, list_processor, input_dict)

        # Then card processors
        for card_processor in self._card_processors:
            if not self.is_processor(card_processor):
                continue

            type_name = card_processor.name
            # process all cards of the given type name individually
            cards = self.get_cards(type_name)

            for card in cards:
                input_dict = {'card': card}
                self.execute_processor(github, card_processor, input_dict)

        self.__log.close_context()
