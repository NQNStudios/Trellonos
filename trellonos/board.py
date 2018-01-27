import re

from list import List
import logtools as log


METADATA_REGEX = re.compile('^<.+>$')

# Single underscore attributes to avoid mangling-related error
# Because these fields will be set dynamically (hence the dictionary)
SPECIAL_META_LISTS = {
    'Archetypes': '_archetypes',
    'Board Processors': '_board_processors',
    'List Processors': '_list_processors',
    'Regex List Processors': '_regex_list_processors',
    'List Defaults': '_list_defaults',
    'Card Processors': '_card_processors'
}


class Board(object):
    """ Wrapper of a Trello board """

    def __init__(self, trello, trello_board, meta_board=None):
        self._trello = trello
        self._board_data = trello_board
        self._meta_board = meta_board

        self._lists = {}

        self._meta_lists = {}

        # Set special meta lists to empty before they are found
        for list_name in SPECIAL_META_LISTS:
            setattr(self, SPECIAL_META_LISTS[list_name], {})

        # retrieve lists in the board
        trello_lists = trello.get_lists(trello_board)

        # First retrieve meta lists
        meta_lists = []
        self._is_meta = False
        if meta_board != None:
            meta_lists = trello.get_lists(meta_board)
            self._is_meta = True

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
                self._meta_lists[list_name] = meta_list_object

            # closed meta lists will be discarded altogether by API filter

        # map regular lists in a dictionary by name
        for trello_list in trello_lists:
            list_name = trello_list['name']

            list_object = List(trello, self, trello_list, self._is_meta)

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
    def is_meta(self):
        return self._is_meta
 
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
        return self._meta_lists

    def update_trello_instance(self, trello):
        self._trello = trello
        for list in self._lists:
            self.lists[list]._trello = trello
            for card in self.lists[list].cards:
                card._trello = trello

    def create_list(self, name):
        """ Creates a list in this board. Adds the list to this
        board's dictionary and returns the Trellonos wrapper object """

        trello_list = self._trello.create_list(self._board_data, name)

        new_list = List(self._trello, self, trello_list)
        self._lists[name] = new_list

        return new_list

    def sort_list(self, list_object, position):
        """ Sorts the given list (supplied as Trellonos  wrapper) to the given
        position. Position can be 'top', 'bottom', or a positive number """

        list_object.sort(self._trello, position)

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
            for card in tlist.cards:
                # Add the card if it matches OR if we want all cards
                if type_name == '<All>' or card.type_name == type_name:
                    cards.append(card)

        return cards

    def execute_processor(self, script_manager, github, processor, input):
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
        input['log'] = log

        # Pass the Trello wrapper into the processor
        input['trello'] = self._trello

        # Pass the GithubManager into the processor as input
        input['github'] = github

        # Pass the whole processor card into the processor as input
        # (For access to things such as checklists)
        input['processor'] = processor

        # Pass the scriptmanager to processor as input (for access to
        # markup evaluation)
        # TODO is this secure?
        input['script_manager'] = script_manager

        # Return the output dictionary
        return github.execute_gist(script_manager, gist_id, gist_file, input)

    def process(self, trellonos, github, script_manager):
        """ Run each of this board's many types of processors """
        if len(self.meta_lists) == 0:
            log.message('Board ' + self.name + ' has no meta lists and won\'t be processed.')
            return

        log.open_context('Processing board ' + self.name)

        # first, processors of the whole board
        for board_processor in self._board_processors:
            # send the board as an argument, and trello wrapper
            input_dict = {'board': self}

            # execute the board processor
            self.execute_processor(script_manager, github, board_processor, input_dict)

        # Then list processors
        for list_processor in self._list_processors:
            list_name = list_processor.name
            input_list = self._lists[list_name]

            # Pass the list with the same name as an argument
            input_dict = {'list': input_list}
            self.execute_processor(script_manager, github, list_processor, input_dict)

        # Then regex list processors
        for regex_processor in self._regex_list_processors:
            # retrieve the regex
            list_regex = re.compile(regex_processor.name)

            # run a loop to find all the lists matching the regex
            matching_lists = []

            for list_name in self._lists:
                if re.search(list_regex, list_name):
                    matching_lists.append(self._lists[list_name])

            # now process each matching list
            for input_list in matching_lists:
                input_dict = {'list': input_list}
                self.execute_processor(script_manager, github, regex_processor, input_dict)

        # Then card processors
        for card_processor in self._card_processors:
            type_name = card_processor.name
            # process all cards of the given type name individually
            cards = self.get_cards(type_name)

            for card in cards:
                input_dict = {'card': card}
                self.execute_processor(script_manager, github, card_processor, input_dict)

        log.close_context()

    # Markup functions
    def fill_cards_markup(self, script_manager):
        """ Fill all markup expressions in cards contained by this board """
        for name in self.lists:
            self.lists[name].fill_cards_markup(script_manager)

