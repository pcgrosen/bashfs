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

    return parser.parse_args()


def main():
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    options = parse_args()
    operations = BashFS()

    fuse_options = set(pyfuse3.default_options)
    fuse_options.add("fsname=bashfs")
    fuse_options.discard("default_permissions")
    if options.debug_fuse:
        fuse_options.add("debug")
    pyfuse3.init(operations, options.mountpoint, fuse_options)

    try:
        trio.run(pyfuse3.main)
    except:
        pyfuse3.close(unmount=True)
        raise

    pyfuse3.close()


main()
