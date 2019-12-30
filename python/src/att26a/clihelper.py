import argparse
import logging

def get_verbose_level(vs):
    if vs >= 2:
        return logging.DEBUG
    elif vs >= 1:
        return logging.INFO
    else:
        return logging.WARNING

# https://stackoverflow.com/questions/6076690/verbose-level-with-argparse-and-multiple-v-options
class VAction(argparse.Action):
    def __init__(self, option_strings, dest, nargs=None, const=None,
                 default=None, type=None, choices=None, required=False,
                 help=None, metavar=None):
        super(VAction, self).__init__(option_strings, dest, nargs, const,
                                      default, type, choices, required,
                                      help, metavar)
        self.values = 0
    def __call__(self, parser, args, values, option_string=None):
        if values is None:
            self.values += 1
        else:
            try:
                self.values = int(values)
            except ValueError:
                self.values = values.count('v')+1
        setattr(args, self.dest, self.values)

def setup_standard_demo_cli(progdesc, demo_function):
    from . import CanNotOpenDeviceError
    parser = argparse.ArgumentParser(description=progdesc)
    parser.add_argument('-v', nargs='?', action=VAction, dest='verbose', default=0,
                        help="Provide debug information. More than one v supported")
    parser.add_argument('devname', metavar='dev', type=str,
                        help='the Serial Device that connects to the AT&T 26A.')
    args = parser.parse_args()

    import logging
    loglevel = get_verbose_level(args.verbose)
    logging.basicConfig(level=loglevel)
    logging.getLogger('att26a').setLevel(loglevel)

    try:
        demo_function(args.devname)
    except CanNotOpenDeviceError as e:
        print("ERROR:", str(e))
        exit(1)
