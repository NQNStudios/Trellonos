from trello import TrelloApi


FIELDS_NAME_ONLY = ['name']
FIELDS_DEFAULT = ['name', 'closed']

FILTER_OPEN = 'open'
FILTER_CLOSED = 'closed'
FILTER_ALL = 'all'
FILTER_DEFAULT = FILTER_ALL


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


class Trello(object):
    """ Wrapper of the Trello API """

    def __init__(self, api_key, token=None):
        self.trello = TrelloApi(api_key, token)

        self.member = self.trello.members.get('me')

    @staticmethod
    def __filter(filter_function, iterable):
        """ Filters a container based on an optional filter function """

        new_list = list(iterable)

        if filter_function:
            new_list = filter(filter_function, new_list)

        return new_list

    def get_boards(self, board_filter=FILTER_DEFAULT, filter_function=None,
                   fields=FIELDS_DEFAULT):
        """ Retrieves an optionally filtered list of Trello boards """

        boards = self.trello.members.get_board(
            self.member['id'], filter=board_filter, fields=fields)

        boards = self.__filter(filter_function, boards)

        return boards

    def get_board(self, name):
        """ Retrieves the first board with the given name """

        filter = filter_by_name_function(name)

        return self.get_boards(filter)[0]

    def get_lists(self, board, list_filter=FILTER_DEFAULT, filter_function=None,
                  fields=FIELDS_DEFAULT):
        """ Retrieves an optionally filtered list of Trello lists """

        lists = self.trello.boards.get_list(board['id'],
                                            filter=list_filter, fields=fields)

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

    def get_cards(self, list, card_filter=FILTER_DEFAULT, filter_function=None,
                  fields=None):
        """ Retrieves cards from the given list """

        cards = self.trello.lists.get_card(list['id'],
                                           filter=card_filter, fields=fields)

        cards = self.__filter(filter_function, cards)

        return cards
