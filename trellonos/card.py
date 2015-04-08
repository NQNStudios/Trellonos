import yaml
import string
import re


DIVIDER_REGEX = re.compile('^-+$')  # Any natural number of hyphens
DIVIDER_LINE = '---\n'  # splits description plaintext and YAML


class Card(object):

    def __init__(self, trello_card):
        self.__card_data = trello_card

        desc = trello_card['desc']  # retrieve full description including yaml

        desc_lines = ''
        yaml_lines = ''

        yaml_line = False

        for line in string.split(desc, '\n'):
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

    @property
    def name(self):
        return self.__card_data['name']

    @property
    def type_name(self):
        """ The type name of this card (for archetypal inheritance) """
        if 'type' not in self.__yaml_data:
            return None
        else:
            return self.__yaml_data['type']

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
            if key not in self.__inherited_data:
                uninherited_yaml_data[key] = self.__yaml_data[key]

        yaml_lines = yaml.dump(uninherited_yaml_data, default_flow_style=False)

        return self.description + DIVIDER_LINE + yaml_lines

    @property
    def yaml_data(self):
        return self.__yaml_data

    def apply_archetype(self, archetype_card):
        """ Inherit the given archetype's yaml_data """
        self.__inherited_data = []
        yaml_data = archetype_card.yaml_data

        for key in yaml_data:
            if key not in self.__yaml_data:
                self.__yaml_data[key] = yaml_data[key]
                self.__inherited_data.append(key)
