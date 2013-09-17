from .server import Server


if __name__ == '__main__':
    from argparse import ArgumentParser

    argp = ArgumentParser(description='xtas-lite server')
    argp.add_argument('--debug', action='store_true')

    args = argp.parse_args()

    server = Server(debug=args.debug)
    server.run()
