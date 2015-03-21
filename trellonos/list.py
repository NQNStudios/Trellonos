from card import Card


class List(object):

    def __init__(self, trello, trello_list):
        self.__list_data = trello_list

        self.__cards = []

        for trello_card in trello.get_cards(trello_list):
            self.__cards.append(Card(trello_card))

    @property
    def cards(self):
        return self.__cards

    def get_card(self, name):
        for card in self.cards:
            if card.name == name:
                return card

    def apply_archetypes(self, archetypes):
        for card in self.cards:
            if 'type' in card.yaml_data:
                type_name = card.yaml_data['type']
                archetype = archetypes.get_card(type_name)

                card.apply_archetype(archetype)

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
