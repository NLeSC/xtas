# Generate xtas configuration file.


if __name__ == '__main__':
    import argparse
    from os.path import abspath, dirname, join
    from shutil import copyfileobj
    import sys

    parser = argparse.ArgumentParser(description=
                                     'Make xtas configuration file.')
    parser.add_argument('-o', dest='output', default='xtas_config.py')
    args = parser.parse_args()

    with open(join(dirname(__file__), '..', 'config.py')) as default:
        # XXX in Python 3, we can make this safer by opening with 'x'
        with open(args.output, 'w') as out:
            copyfileobj(default, out)
            print("Generated configuration file at %r" % args.output)
