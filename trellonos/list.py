from card import Card


class List(object):

    def __init__(self, trello, trello_list):
        self.__list_data = trello_list

        self.__cards = []

        # store contained cards in a list
        for trello_card in trello.get_cards(trello_list):
            # in Trellonos form
            self.__cards.append(Card(trello_card))

    @property
    def cards(self):
        return self.__cards

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
        for card in self.cards:
            if 'type' in card.yaml_data:
                type_name = card.yaml_data['type']
                archetype = archetypes.get_card(type_name)

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
