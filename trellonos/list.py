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
        # Retrieve the list default metacard
        default_card = self.get_card('<Default>')

        for card in self.cards:
            type_name = ''

            # If the card defines a type, use that archetype
            if 'type' in card.yaml_data:
                type_name = card.yaml_data['type']

            # If not, use the list default if it exists
            elif default_card:
                print('using a default card')
                type_name = default_card.yaml_data['type']
                print(type_name)

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
