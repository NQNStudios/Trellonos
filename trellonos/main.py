from trellotools import Trello
from githubtools import GithubManager
from trellonos import Trellonos

if __name__ == "__main__":
    # Create Trello API and Github API wrappers from environment vars
    trello = Trello.from_environment_vars()
    github = GithubManager.from_environment_vars()

    # Construct a Trellonos object using these components
    trellonos = Trellonos(trello, github)

    # Run Trellonos processing
    trellonos.process()
