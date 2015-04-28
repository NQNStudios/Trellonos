from card import Card


class List(object):

    def __init__(self, trello, parent_board, trello_list):
        self.__parent_board = parent_board
        self.__list_data = trello_list

        self.__cards = []
        self.__closed_cards = []

        # store contained cards in a list
        for trello_card in trello.get_cards(trello_list):
            # in trellonos form
            card = Card(self, trello_card)

            # separated open/closed
            if card.open:
                self.__cards.append(card)
            else:
                self.__closed_cards.append(card)

    @property
    def name(self):
        return self.__list_data['name']

    @property
    def open(self):
        return not self.__list_data['closed']

    @property
    def closed(self):
        return self.__list_data['closed']

    @property
    def position(self):
        return self.__list_data['pos']

    def sort(self, trello, position):
        self.__list_data['pos'] = position
        trello.sort_list(self.__list_data, position)

    def archive(self, trello):
        # Update self-contained data to reflect this call
        self.__list_data['closed'] = True

        # Trello API call to archive
        trello.update_list_closed(self.__list_data, True)

        # Move this list to the parent's dictionary of closed lists
        self.__parent_board.lists.pop(self.name)
        self.__parent_board.closed_lists[self.name] = self

    def unarchive(self, trello):
        # Update self-contained data
        self.__list_data['closed'] = False

        # Trello API call to unarchive
        trello.update_list_closed(self.__list_data, False)

        # Move this list to the parent's dictionary of open lists
        self.__parent_board.closed_lists.pop(self.name)
        self.__parent_board.lists[self.name] = self

    @property
    def cards(self):
        return self.__cards

    @property
    def closed_cards(self):
        return self.__closed_cards

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

    # List functions
    def __getitem__(self, index):
        return self.__cards[index]

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
