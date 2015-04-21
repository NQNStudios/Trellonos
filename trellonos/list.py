from card import Card


class List(object):

    def __init__(self, trello, trello_list):
        self.__list_data = trello_list

        self.__cards = []
        self.__closed_cards = []

        # store contained cards in a list
        for trello_card in trello.get_cards(trello_list):
            # in trellonos form
            card = Card(trello_card)

            # separated open/closed
            if card.open:
                self.__cards.append(card)
            else:
                self.__closed_cards.append(card)

    @property
    def open(self):
        return not self.__list_data['closed']

    @property
    def closed(self):
        return self.__list_data['closed']

    def archive(self, trello):
        self.__list_data['closed'] = True
        trello.update_list_closed(self.__list_data, True)

    def unarchive(self, trello):
        self.__list_data['closed'] = False
        trello.update_list_closed(self.__list_data, False)

    @property
    def cards(self):
        return self.__cards

    @property
    def closed_cards(self):
        return self.__closed_cards

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
