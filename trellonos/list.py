from card import Card


class List(object):

    def __init__(self, trello, parent_board, trello_list):
        self.__parent_board = parent_board
        self._list_data = trello_list

        self._cards = []
        self.__closed_cards = []

        # store contained cards in a list
        for trello_card in trello.get_cards(trello_list):
            # in trellonos form
            card = Card(self, trello_card)

            # separated open/closed
            if card.open:
                self._cards.append(card)
            else:
                self.__closed_cards.append(card)

    @property
    def name(self):
        return self._list_data['name']

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

    def sort(self, trello, position):
        self._list_data['pos'] = position
        trello.sort_list(self._list_data, position)

    def archive(self, trello):
        # Update self-contained data to reflect this call
        self._list_data['closed'] = True

        # Trello API call to archive
        trello.update_list_closed(self._list_data, True)

        # Remove this list from the parent board's dictionary
        self.__parent_board.lists.pop(self.name)

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
        new_card = Card(self, trello_card)
        self._cards.append(new_card)

        return new_card

    def apply_archetypes(self, archetypes):
        """ Applies the given archetypes to all pertinent cards in this list """

        # Retrieve the list default metacard
        default_card = self.get_card('<Default>')

        for card in self.cards:
            type_name = ''

            # If the card defines a type, use that archetype
            if 'type' in card.yaml_data:
                type_name = card.yaml_data['type']

            # If not, use the list default if it exists
            elif default_card:
                type_name = default_card.yaml_data['type']

            # attempt to retrieve the archetype
            archetype = archetypes.get_card(type_name)

            # apply it if it exists
            if archetype:
                card.apply_archetype(archetype)

    def copy(self, trello, destination_board=None):
        """ Copies this list in the given Trellonos board or the same board """
        if not destination_board:
            destination_board = self.__parent_board

        # Make the API call
        new_list = trello.copy_list(self._list_data,
                                    destination_board._board_data)

        # Make the wrapper
        list_object = List(destination_board, new_list)
        # Add the wrapper to the destination board's container
        destination_board._lists[list_object.name] = list_object

    def copy_contents(self, trello, destination_list):
        """ Copies the cards contained in this list into the given Trellonos
        list """

        for card in self._cards:
            card.copy(trello, destination_list)

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
