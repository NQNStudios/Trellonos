from trello import TrelloApi
import requests


FILTER_OPEN = 'open'
FILTER_CLOSED = 'closed'
FILTER_ALL = 'all'
FILTER_DEFAULT = FILTER_ALL


# FILTER FUNCTIONS

def filter_by_name_function(name):
    """ Creates a filter function to filter objects by name """

    def filter(trello_object):
        return trello_object['name'] == name

    return filter


def filter_by_keyword_function(keyword):
    """ Creates a filter function to filter for objects containing keyword """

    def filter(trello_object):
        return trello_object['name'].count(keyword)

    return filter

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

    @staticmethod
    def __filter(filter_function, iterable):
        """ Filters a container based on an optional filter function """

        new_list = list(iterable)

        if filter_function:
            new_list = filter(filter_function, new_list)

        return new_list

    # REQUESTS HELPERS #

    def request_params(self, extra_params={}):

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

    def get_boards(self, board_filter=FILTER_DEFAULT, filter_function=None):
        """ Retrieves an optionally filtered list of Trello boards """

        boards = self.__trello.members.get_board(
            self.__member['id'], filter=board_filter)

        boards = self.__filter(filter_function, boards)

        return boards

    def get_board(self, name):
        """ Retrieves the first board with the given name """

        filter = filter_by_name_function(name)

        return self.get_boards(filter)[0]

    def update_board_closed(self, board, value):
        self.__trello.boards.update_closed(board['id'],
                                           boolean_to_string(value))

    # LISTS #

    def get_lists(self, board, list_filter=FILTER_DEFAULT,
                  filter_function=None):
        """ Retrieves an optionally filtered list of Trello lists """

        lists = self.__trello.boards.get_list(board['id'], filter=list_filter)

        lists = self.__filter(filter_function, lists)
        return lists

    def get_lists_with_keyword(self, board, keyword):
        """ Retrieves a list of lists with title containing the given
        keyword """

        filter = filter_by_keyword_function(keyword)

        return self.get_lists(board, filter)

    def get_list(self, board, name):
        """ Retrieves the first list with the given title """

        filter = filter_by_name_function(name)

        return self.get_lists(board, filter)[0]

    def update_list_closed(self, list, value):
        """ Opens or closes a list """
        self.__trello.lists.update_closed(list['id'],
                                          boolean_to_string(value))

    def create_list(self, board, list_name):
        """ Creates a new list in the given board """
        return self.__trello.boards.new_list(board['id'], list_name)

    # CARDS #

    def get_cards(self, list, card_filter=FILTER_DEFAULT, filter_function=None,
                  fields=None):
        """ Retrieves cards from the given list """

        cards = self.__trello.lists.get_card(
            list['id'], filter=card_filter, fields=fields)

        cards = self.__filter(filter_function, cards)

        return cards

    def update_card_closed(self, card, value):
        self.__trello.cards.update_closed(card['id'],
                                          boolean_to_string(value))
