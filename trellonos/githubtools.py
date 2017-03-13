import os

from github import Github
import logtools as log


class SecurityException(Exception):
    pass


class GithubManager(object):
    """ Wrapper for Github operations, specifically retrieving scripts from
    gists """

    def __init__(self, username, password):
        self.__github = Github(username, password)

    @classmethod
    def from_environment_vars(cls):
        # Construct a Github wrapper using environment variable settings
        username = os.environ['GITHUB_USER']
        password = os.environ['GITHUB_PASSWORD']
        return cls(username, password)

    def execute_gist(self, scriptManager, id, filename, input={},
                     continue_on_error=True):

        """ Run the Python code contained in the given gist file
        in a safe context. Errors will be ignored (after stopping execution)
        if continue_on_error is true. An exception will be raised if
        continue_on_error is false.
        """

        log.open_context('Script ' + filename + ' from gist ' + id)

        # retrieve the gist
        gist = self.__github.get_gist(id)

        # security check
        if gist.public:
            raise SecurityException('Error: attempted to run public code')

        # extract the script
        script = gist.files[filename].content

        output = scriptManager.execute(script, input, continue_on_error)
        log.close_context()

        return output

