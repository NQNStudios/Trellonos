import string
import re

import yaml
import dateutil.parser

DIVIDER_REGEX = re.compile('^-+$')  # Any natural number of hyphens
DIVIDER_LINE = '---\n'  # splits description plaintext and YAML


class Card(object):
    """ Wrapper of a Trello card """

    def parse_description(self, description):
        """ Helper function updates this card's yaml data based on the new
        description supplied """

        desc_lines = ''
        yaml_lines = ''

        yaml_line = False

        for line in string.split(description, '\n'):
            if re.search(DIVIDER_REGEX, line):
                # After the yaml divider is discovered, all lines are YAML
                yaml_line = True
                continue

            line += '\n'  # preserve line breaks

            if yaml_line:
                yaml_lines += line
            else:
                desc_lines += line

        # update description stripped of yaml
        self.__card_data['desc'] = desc_lines

        self.__yaml_lines = yaml_lines  # save source yaml for future updates
        self.__yaml_data = yaml.load(yaml_lines)  # parse yaml attributes

        if not self.__yaml_data:
            self.__yaml_data = {}  # no null yaml data

    def __init__(self, parent_list, trello_card):
        """ Constructs a Trellonos wrapper of the given card in the given
        parent list """
        self.__parent_list = parent_list
        self.__card_data = trello_card
        self.__inherited_data = []

        desc = trello_card['desc']  # retrieve full description including yaml

        self.parse_description(desc)

    @property
    def name(self):
        return self.__card_data['name']

    @property
    def open(self):
        return not self.__card_data['closed']

    @property
    def closed(self):
        return self.__card_data['closed']

    @property
    def due_date(self):
        if 'due' in self.__card_data:
            if self.__card_data['due']:
                return dateutil.parser.parse(self.__card_data['due'])

    @property
    def type_name(self):
        """ The type name of this card (for archetypal inheritance) """
        if 'type' not in self.__yaml_data:
            return None
        else:
            return self.__yaml_data['type']

    @type_name.setter
    def type_name(self, value):
        self.__yaml_data['type'] = value

    @property
    def description(self):
        """ The trimmed description of this card (excluding yaml_data) """
        return self.__card_data['desc']

    @property
    def full_description(self):
        """ The full description of this card including new yaml_data but not
        inherited yaml_data """

        uninherited_yaml_data = {}
        for key in self.__yaml_data:
            if self.__inherited_data and key not in self.__inherited_data:
                uninherited_yaml_data[key] = self.__yaml_data[key]

        yaml_lines = yaml.safe_dump(uninherited_yaml_data,
                                    encoding='utf-8', allow_unicode=True,
                                    default_flow_style=False)

        return self.description + DIVIDER_LINE + yaml_lines

    @property
    def yaml_data(self):
        return self.__yaml_data

    def set_description(self, trello, full_description):
        """ Gives this card a new description """
        # Change the description through API call
        trello.update_card_description(self.__card_data, full_description)

        # Parse out Yaml data from the new description
        self.parse_description(full_description)

    def update_description(self, trello):
        """ Updates this card's description to persist new changes to YAML
        data and (less often) the description field """
        full_description = self.full_description

        trello.update_card_description(self.__card_data, full_description)

    def apply_default_type(self, default_type):
        if not self.type_name:
            self.__inherited_data.append('type')
            self.type_name = default_type

    def apply_archetype(self, archetype_card):
        """ Inherit the given archetype's yaml_data """
        yaml_data = archetype_card.yaml_data

        for key in yaml_data:
            if key not in self.__yaml_data:
                self.__yaml_data[key] = yaml_data[key]
                self.__inherited_data.append(key)

    def archive(self, trello):
        # update card data to reflect change
        self.__card_data['closed'] = True

        # make the change through API call
        trello.update_card_closed(self.__card_data, True)

        # Move to the proper parent container
        self.__parent_list.cards.remove(self)
        self.__parent_list.closed_cards.append(self)

    def unarchive(self, trello):
        # update card data to reflect change
        self.__card_data['closed'] = False

        # make the change through API call
        trello.update_card_closed(self.__card_data, False)

        # Move to the proper parent container
        self.__parent_list.closed_cards.remove(self)
        self.__parent_list.cards.append(self)

    def move(self, trello, destination_list):
        # TODO this is a hack which moves cards by copying them, then
        # archiving the original. It's done this way because the API card
        # movement functions seem to be broken
        self.copy(trello, destination_list)
        self.archive(trello)

    def copy(self, trello, destination_list=None, override_params={}):
        """ Copies this Card in the given Trellonos list or the same list """
        if not destination_list:
            destination_list = self.__parent_list

        # Make the API call
        new_card = trello.copy_card(self.__card_data,
                                    destination_list._list_data,
                                    override_params)

        # Make the wrapper
        card_object = Card(destination_list, new_card)
        # Add the wrapper to the destination list's container
        destination_list._cards.append(card_object)

        return card_object
