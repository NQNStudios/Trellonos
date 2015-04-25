import unittest

import trellotools
from trellotools import Trello


class TrelloToolsTestCase(unittest.TestCase):
    """ Tests the trellotools module from top to bottom """

    # HELPERS AND INITIALIZATION

    def setUp(self):
        # Create an API wrapper object
        self.trello = Trello.from_environment_vars()

        # Retrieve the test board for convenience of other tests
        self.test_board = None

        boards = self.trello.get_boards()

        for board in boards:
            if board['name'] == 'Trellonos Tests':
                self.test_board = board

    def get_all_lists(self):
        return self.trello.get_lists(self.test_board, trellotools.FILTER_ALL)

    def all_list_count(self):
        return len(self.get_all_lists())

    def get_open_lists(self):
        return self.trello.get_lists(self.test_board, trellotools.FILTER_OPEN)

    def open_list_count(self):
        return len(self.get_open_lists())

    def get_closed_lists(self):
        return self.trello.get_lists(self.test_board, trellotools.FILTER_CLOSED)

    def closed_list_count(self):
        return len(self.get_closed_lists())

    # TEST MODULE HELPERS

    def test_boolean_to_string(self):
        self.assertEqual(trellotools.boolean_to_string(True), 'true')
        self.assertEqual(trellotools.boolean_to_string(False), 'false')

    # TEST BOARD FUNCTIONS

    def test_get_boards(self):
        # If we can retrieve the test board, things should be working properly
        self.assertIsNotNone(self.test_board, "Couldn't find the test board.")

    # TEST LIST FUNCTIONS

    def test_get_lists(self):
        all_lists = self.all_list_count()
        open_lists = self.open_list_count()
        closed_lists = self.closed_list_count()

        # There should be at least one of each
        self.assertGreater(open_lists, 0)
        self.assertGreater(closed_lists, 0)

        # There is at least one of each, therefore the total should be
        # greater than both counts
        self.assertGreater(all_lists, open_lists)
        self.assertGreater(all_lists, closed_lists)

        # And the total should equal the sum of both counts
        self.assertEqual(all_lists, open_lists + closed_lists)

    def test_update_list_closed(self):
        open_lists = self.get_open_lists()

        # Make sure we have some open lists
        first_open_count = len(open_lists)
        self.assertGreater(first_open_count, 0)

        # Now close all of them
        for list in open_lists:
            self.trello.update_list_closed(list, True)

        # Now make sure we have none
        self.assertEqual(self.open_list_count(), 0)

        # Now open them again
        for list in open_lists:
            self.trello.update_list_closed(list, False)

        # and make sure we have the same number as before
        self.assertEqual(first_open_count, self.open_list_count())

    def test_create_list(self):
        first_count = self.all_list_count()
        new_list = self.trello.create_list(self.test_board,
                                           'List Creation Test')

        self.assertEqual(self.all_list_count(), first_count + 1)

        self.trello.update_list_closed(new_list, True)

    def test_sort_list(self):
        # Helper function for the test
        def get_test_lists():
            open_lists = self.get_open_lists()

            test_lists = []

            for list in open_lists:
                if 'List Sorting Test' in list['name']:
                    test_lists.append(list)

            return test_lists

        # Obtain a list of lists for the test
        test_lists = get_test_lists()
        num_test_lists = len(test_lists)

        # We need at least 3 for this test
        self.assertGreaterEqual(num_test_lists, 3)

        original_positions = {}
        for i in range(num_test_lists):
            original_positions[i] = test_lists[i]['pos']

        # They should be in ascending order
        for i in range(num_test_lists):
            if i + 1 in original_positions:
                self.assertGreater(original_positions[i + 1],
                                   original_positions[i])

        # Specific tests on first three
        list_a = test_lists[0]
        list_b = test_lists[1]
        list_c = test_lists[2]

        # put first list in between second two
        new_pos = (list_b['pos'] + list_c['pos']) / 2
        self.trello.sort_list(list_a, new_pos)

        # Now check if it worked
        new_test_lists = get_test_lists()
        new_list_a = new_test_lists[0]
        new_list_c = new_test_lists[2]

        self.assertEqual(list_b['pos'], new_list_a['pos'])
        self.assertEqual(list_c['pos'], new_list_c['pos'])

    # TEST CARD FUNCTIONS

    def test_get_cards(self):
        pass

    def test_update_card_closed(self):
        pass

    def test_create_card(self):
        pass

    def test_delete_card(self):
        pass


if __name__ == '__main__':
    unittest.main()
