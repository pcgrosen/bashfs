import trio
import pyfuse3
import logging
from . import BashFS
from argparse import ArgumentParser


def parse_args():
    parser = ArgumentParser()

    parser.add_argument("mountpoint", type=str,
                        help="Where to mount the file system")
    parser.add_argument("--debug", action="store_true", default=False,
                        help="Enable debugging output")
    parser.add_argument("--debug-fuse", action="store_true", default=False,
                        help="Enable FUSE debugging output")

    parser.add_argument("--argv-prefix", action="append",
                        help="The argv array that preceeds the filesystem path."
                        "\nFor example, `--argv-prefix=bash --argv-prefix=-c`"
                        "\nis equivalent to the default.")

    parser.add_argument("--separator", default="|",
                        help="The string to insert between path elements.")

    return parser.parse_args()


def main():
    logging.basicConfig()
    args = parse_args()
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    argv = args.argv_prefix if args.argv_prefix else ("bash", "-c")
    operations = BashFS(argv_prefix=argv, separator=args.separator.encode())

    fuse_options = set(pyfuse3.default_options)
    fuse_options.add("fsname=bashfs")
    fuse_options.discard("default_permissions")
    if args.debug_fuse:
        fuse_options.add("debug")
    pyfuse3.init(operations, args.mountpoint, fuse_options)

    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=True)
        raise

    pyfuse3.close()


main()
