from github import Github


class GithubManager(object):

    def __init__(self, username, password):
        self.__github = Github(username, password)
        self.__interface = {
            'input': {},
            'output': {}
        }

    def execute_gist(self, id, filename, input):
        content = self.__github.get_gist(id).files[filename].content

        self.__interface['input'] = input

        exec(content, self.__interface, {})

        return self.__interface['output']
