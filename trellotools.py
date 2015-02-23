from trello import TrelloApi

NAME_ONLY = [ 'name' ]

class Trello(object):
    def __init__(self, api_key, token=None):
        self.trello = TrelloApi(api_key, token)

        self.member = self.trello.members.get('me')

    @staticmethod
    def __filter(filter_function, iterable):
        new_list = list(iterable)

        if filter_function:
            new_list = filter(filter_function, new_list)

        return new_list

    def get_boards(self, filter_function = None, fields = NAME_ONLY):
        boards = self.trello.members.get_board(self.member['id'], filter='open', fields = fields)
        boards = self.__filter(filter_function, boards)
        return boards

    def get_board(self, name):
        def filter(board):
            return board['name'] == name

        return self.get_boards(filter)[0]

    def get_lists(self, board, filter_function = None, fields = NAME_ONLY):
        lists = self.trello.boards.get_list(board['id'], filter='open', fields = fields)
        lists = self.__filter(filter_function, lists)
        return lists

    def get_lists_with_keyword(self, board, keyword):
        def filter(list):
            return list['name'].count(keyword)

        return self.get_lists(board, filter)

    def get_list(self, board, name):
        def filter(list):
            return list['name'] == name

        return self.get_lists(board, filter)[0]

    def get_cards(self, list, filter_function = None, fields = None):
        cards = self.trello.lists.get_card(list['id'], filter='open', fields = fields)
        cards = self.__filter(filter_function, cards)
        return cards
