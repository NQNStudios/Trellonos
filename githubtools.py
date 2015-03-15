from github import Github


class GithubManager(object):

    def __init__(self, username, password):
        self.github = Github(username, password)

    def execute_gist(self, id, filename, gist_globals=None, gist_locals=None):
        if not gist_globals:
            gist_globals = globals()

        if not gist_locals:
            gist_locals = locals()

        content = self.github.get_gist(id).files[filename].content

        exec(content, gist_globals, gist_locals)
