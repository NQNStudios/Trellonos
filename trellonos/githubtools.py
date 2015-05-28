import os

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

    @classmethod
    def from_environment_vars(cls):
        # Construct a Github wrapper using environment variable settings
        username = os.environ['GITHUB_USER']
        password = os.environ['GITHUB_PASSWORD']
        return cls(username, password)

    def execute_gist(self, id, filename, log, input={},
                     continue_on_error=True):

        """ Run the Python code contained in the given gist file
        in a safe context. Errors will be ignored (after stopping execution)
        if continue_on_error is true. An exception will be raised if
        continue_on_error is false.
        """

        # make a place to store the gist locals
        gist_locals = {}

        log.open_context('Script ' + filename + ' from gist ' + id)

        # retrieve the gist
        gist = self.__github.get_gist(id)

        # security check
        if gist.public:
            raise SecurityException('Error: attempted to run public code')

        self.__interface['input'] = input  # provide the given input
        self.__interface['output'] = {}  # clear previous output

        error = None

        # extract the script lines as an array
        script_lines = gist.files[filename].content.splitlines()

        current_line = 0

        while current_line < len(script_lines):
            script_block = script_lines[current_line]

            # if the line starts a block, process the entire block at once.
            # Do it this way to avoid a syntax error:
            # This allows us to still execute line by line. Blocks just have
            # less precision in the error report.
            if len(script_block) > 0 and script_block.strip()[-1:] == ':':
                i = 1
                while True:
                    if current_line + i >= len(script_lines):
                        break

                    next_line = script_lines[current_line + i]

                    script_block += '\n' + script_lines[current_line + i]
                    i += 1  # almost forgot!

                    if not (next_line[0:4] == '    ' or next_line == ''):
                        break

                current_line += (i - 1)

            try:
                # try to run the line
                exec(script_block, self.__interface, gist_locals)
            except Exception as e:
                # Log the error
                log.message(type(e).__name__ + ' in line ' +
                            str(current_line + 1) + ': ' + str(e))

                for script_line in script_block.splitlines():
                    log.message(script_line)

                error = e
                break

            # increment the line number
            current_line += 1

        if error and not continue_on_error:
            raise error

        log.close_context()

        return self.__interface['output']
