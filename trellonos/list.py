import random
from card import Card


class List(object):

    def __init__(self, trello, parent_board, trello_list):
        self._trello = trello
        self._parent_board = parent_board
        self._list_data = trello_list

        self._cards = []
        self.__closed_cards = []

        # store contained cards in a list
        for trello_card in trello.get_cards(trello_list):
            # in trellonos form
            card = Card(trello, self, trello_card)

            # separated open/closed
            if card.open:
                self._cards.append(card)
            else:
                self.__closed_cards.append(card)

    @property
    def name(self):
        return self._list_data['name']

    @property
    def id(self):
        return self._list_data['id']

    @property
    def open(self):
        return not self._list_data['closed']

    @property
    def closed(self):
        return self._list_data['closed']

    @property
    def position(self):
        return self._list_data['pos']

    @property
    def cards(self):
        return self._cards

    @property
    def closed_cards(self):
        return self.__closed_cards

    def set_name(self, trello, name):
        """ Rename this list """
        # Through the API
        trello.update_list_name(self._list_data, name)
        # In the parent list map
        del self._parent_board.lists[self.name]
        self._parent_board.lists[name] = self
        # In instance fields
        self._list_data['name'] = name

    def sort(self, trello, position):
        self._list_data['pos'] = position
        trello.sort_list(self._list_data, position)

    def archive(self, trello):
        # Update self-contained data to reflect this call
        self._list_data['closed'] = True

        # Trello API call to archive
        trello.update_list_closed(self._list_data, True)

        # Remove this list from the parent board's dictionary
        self._parent_board.lists.pop(self.name)

    def archive_all_cards(self, trello):
        """ Archives all cards in this list that are not already archived """
        for i in reversed(range(len(self.cards))):
            # Loop through the collection in reverse to avoid indexing
            # errors. Don't iterate because archive() will modify the
            # contents of self.cards
            card = self.cards[i]
            card.archive(trello)

    def unarchive_all_cards(self, trello):
        """ Unarchives all archived cards in this list """
        for i in reversed(range(len(self.closed_cards))):
            # Loop in reverse
            card = self.closed_cards[i]
            card.unarchive(trello)

    def get_card(self, name):
        """ Finds the first card in this list with the given name """
        for card in self.cards:
            if card.name == name:
                return card

    def get_cards(self, name):
        """ Returns a list of cards with the given name """
        cards = []

        for card in self.cards:
            if card.name == name:
                cards.append(card)

        return cards

    def create_card(self, trello, name):
        """ Creates a card in this list. Adds the card to this lists's
        container and returns the Trellonos wrapper object """

        trello_card = trello.create_card(self._list_data, name)
        new_card = Card(trello, self, trello_card)
        self._cards.append(new_card)

        return new_card

    def apply_default_type(self, default_type):
        """ Applies the given default type name to every card in this list
        that does not already have a type name, including closed cards """

        for card in self.cards:
            card.apply_default_type(default_type)

        for card in self.closed_cards:
            card.apply_default_type(default_type)

    def apply_archetypes(self, archetypes):
        """ Applies the given archetypes to all pertinent cards in this list """

        for card in self.cards:
            type_name = ''

            # If the card defines a type, use that archetype
            if 'type' in card.yaml_data:
                type_name = card.yaml_data['type']

            # attempt to retrieve the archetype
            archetype = archetypes.get_card(type_name)

            # apply it if it exists
            if archetype:
                card.apply_archetype(archetype)

    def copy(self, trello, destination_board=None, override_params={}):
        """ Copies this list in the given Trellonos board or the same board """
        if not destination_board:
            destination_board = self._parent_board

        # Make the API call
        new_list = trello.copy_list(self._list_data,
                                    destination_board._board_data,
                                    override_params)

        # Make the wrapper
        list_object = List(self._trello, destination_board, new_list)
        # Add the wrapper to the destination board's container
        destination_board._lists[list_object.name] = list_object

    def copy_contents(self, trello, destination_list):
        """ Copies the cards contained in this list into the given Trellonos
        list """

        for card in self._cards:
            card.copy(trello, destination_list)

    def random_card(self):
        ''' Just return a random card from this list '''
        return self.cards[random.randrange(len(self.cards))]

    # List functions
    def __getitem__(self, index):
        return self._cards[index]

    # Iterator functions
    def __iter__(self):
        self.__index = 0
        return self

    def next(self):
        if self.__index >= len(self.cards):
            raise StopIteration
        else:
            self.__index += 1
            return self.cards[self.__index - 1]

    # Markup functions
    def fill_cards_markup(self, scriptManager):
        """ Fill in all markup expressions in cards contained by this list """
        for card in self.cards:
            card.fill_markup(scriptManager)
