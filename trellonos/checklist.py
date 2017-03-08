class Checklist(object):
    """ Wrapper class for a Trello checklist attached to a card """

    def __init__(self, checklist_data):
        self._name = checklist_data['name']

        # Store check items as a dictionary of bools for easy lookup
        self._checkitems = {}
        for check_item in checklist_data['checkItems']:
            name = check_item['name']
            status = check_item['state']

            is_complete = (not status == 'incomplete')

            self._checkitems[name] = is_complete

    @property
    def name(self):
        return self._name

    @property
    def check_items(self):
        """ Return a dictionary of items on the checklist, containing their
        completion state as a bool """
        return self._checkitems

    def is_checked(self, item_name):
        return item_name in self._checkitems and self._checkitems[item_name]
