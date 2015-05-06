import os
import json

from trello import TrelloApi
import requests

API_VERSION = '1'
BASE_URL = 'https://api.trello.com/' + API_VERSION + '/'

FILTER_OPEN = 'open'
FILTER_CLOSED = 'closed'
FILTER_ALL = 'all'

# CONVENIENCE CONVERSION FUNCTIONS


def boolean_to_string(boolean):
    if boolean:
        return "true"
    else:
        return "false"


class Trello(object):
    """ Wrapper of the Trello API """

    def __init__(self, api_key, token=None):
        # Store the API key and token for things the Python API can't do
        self.__api_key = api_key
        self.__token = token

        # Make a Trello Python API wrapper object for the things it CAN do
        self.__trello = TrelloApi(api_key, token)

        # Retrieve this Trello user
        self.__member = self.__trello.members.get('me')

    @classmethod
    def from_environment_vars(cls):
        # Construct a Trello wrapper using environment variable settings
        api_key = os.environ['TRELLONOS_API_KEY']
        token = os.environ['TRELLONOS_TOKEN']
        return cls(api_key, token)

    # REQUESTS HELPERS #

    def request_params(self, extra_params={}):
        """ Generates the params dictionary for a trello HTTP request of the
        given parameters. """

        # Add the authentification params
        params = {
            'key': self.__api_key,
            'token': self.__token
        }

        # Add the given params
        for param in extra_params:
            params[param] = extra_params[param]

        return params

    # BOARDS #

    def get_boards(self, board_filter=FILTER_OPEN):
        """ Retrieves an optionally filtered list of Trello boards """

        boards = self.__trello.members.get_board(
            self.__member['id'], filter=board_filter)

        return boards

    # LISTS #

    def get_lists(self, board, list_filter=FILTER_OPEN):
        """ Retrieves an optionally filtered list of Trello lists """

        lists = self.__trello.boards.get_list(board['id'], filter=list_filter)

        return lists

    def update_list_closed(self, list, value):
        """ Opens or closes a list """
        self.__trello.lists.update_closed(list['id'],
                                          boolean_to_string(value))

    def create_list(self, board, list_name):
        """ Creates a new list in the given board """
        return self.__trello.boards.new_list(board['id'], list_name)

    def sort_list(self, list, position):
        """ Sorts the given list to the given position. Position can be
        'top' or 'bottom' or a positive number """

        url = BASE_URL + 'lists/' + list['id'] + '/pos'
        requests.put(url, params=self.request_params({'value': position}))

    def copy_list(self, list, board, override_params={}):
        """ Copies the given list into a new list in the given board """
        url = BASE_URL + 'lists/'

        params = {}

        params['name'] = list['name']
        params['idBoard'] = board['id']
        params['idListSource'] = list['id']

        for override_param in override_params:
            params[override_param] = override_params[override_param]

        # TODO is this supposed to be 'data' or 'params'?
        request = requests.post(url, data=self.request_params(params))

        # Return the output
        return json.loads(request.text)

    # CARDS #

    def get_cards(self, list, card_filter=FILTER_ALL, fields=None):
        """ Retrieves cards from the given list """

        cards = self.__trello.lists.get_card(
            list['id'], filter=card_filter, fields=fields)

        return cards

    def update_card_closed(self, card, value):
        self.__trello.cards.update_closed(card['id'],
                                          boolean_to_string(value))

    def create_card(self, list, card_name, description=''):
        return self.__trello.cards.new(card_name, list['id'], description)

    def delete_card(self, card):
        self.__trello.cards.delete(card['id'])

    def copy_card(self, card, list, override_params={}):
        """ Copies the given card into a new card in the given list """
        url = BASE_URL + 'cards/'

        params = {}

        params['due'] = card['due']
        params['idList'] = list['id']
        params['urlSource'] = 'null'
        params['idCardSource'] = card['id']

        for override_param in override_params:
            params[override_param] = override_params[override_param]

        request = requests.post(url, data=self.request_params(params))

        # Return the output
        return json.loads(request.text)
