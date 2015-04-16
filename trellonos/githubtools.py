from github import Github


class SecurityException(Exception):
    pass


class GithubManager(object):
    """ Wrapper for Github operations, specifically the embedded execution of
    gists """

    def __init__(self, username, password):
        self.__github = Github(username, password)

        # pass data into and out of the gists we run
        self.__interface = {
            'input': {},
            'output': {}
        }

    def execute_gist(self, id, filename, input={}):
        """ Run the Python code contained in the given gist file """

        gist = self.__github.get_gist(id)

        if gist.public:
            raise SecurityException('Error: attempted to run public code')

        content = gist.files[filename].content

        self.__interface['input'] = input  # provide the given input
        self.__interface['output'] = {}  # clear previous output

        exec(content, self.__interface, {})

        return self.__interface['output']
