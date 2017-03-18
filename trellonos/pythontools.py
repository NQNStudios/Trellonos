import logtools as log
import re

class ScriptManager(object):
    """ Wrapper for the execution of embedded Python code in a hopefully
    secure enough way """

    def __init__(self, trellonos):
        self._trellonos = trellonos
        # pass data into and out of the scripts and expressions we run
        self.__interface = {
            'input': {},
            'output': {}
        }

    def execute(self, code, input={}, continue_on_error=True):
        self.__interface['input'] = input  # provide the given input
        self.__interface['output'] = {}  # clear previous output

        error = None

        # make a place to store the script locals
        script_locals = {}

        # Split the code up by lines
        script_lines = code.splitlines()

        # Track the current line for error reporting
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

                    # If the next line is tab-shifted left, end the block
                    if not (next_line[0:4] == '    ' or next_line == ''):
                        # Unless it is an elif: or an else: line
                        if not (next_line[0:5] == 'else:' or
                                next_line[0:5] == 'elif:'):
                            break

                current_line += (i - 1)

            try:
                # try to run the line
                exec(script_block, self.__interface, script_locals)
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

        return self.__interface['output']

    def evaluate_expression(self, expression):
        """ Evaluate a single python expression and return the result """
        log.open_context('Evaluating expression ' + expression)

        # We need to store the result somewhere so we can return it
        prefix = "output['result'] = "
        # Execute the expression with the given Trellonos object as the only
        # input
        result = self.execute(
            prefix + expression, { 'trellonos': self._trellonos })

        log.close_context()

        return result['result']

    def evaluate_markup(self, text):
        """ Return the given string with all markup expressions evaluated
        and filled in """

        # Markup expressions are contained in double braces {{ expression }}
        markup_regex = re.compile('\{\{.+\}\}')

        for match in re.findall(markup_regex, text):
            print(match)
            text = text.replace(
                match,
                self.evaluate_expression(
                        "input['trellonos']." + match[2:-2].strip()))

        return text
