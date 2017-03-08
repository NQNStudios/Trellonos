from trellonos import Trellonos

if __name__ == "__main__":
    # Construct a Trellonos object from environment variables
    trellonos = Trellonos.from_environment_vars()

    # TODO debug
    print(trellonos.evaluate_markup("{{boards['Planner'].lists['TODO'].cards[0].name}}"))

    # Run Trellonos processing
    # trellonos.process()

    # Dump all console output to a Trello card
    # trellonos.dump_log()
