from trellonos import Trellonos

if __name__ == "__main__":
    # Construct a Trellonos object from environment variables
    trellonos = Trellonos.from_environment_vars()

    # Run Trellonos processing
    trellonos.process()

    # Dump all console output to a Trello card
    trellonos.dump_log()
