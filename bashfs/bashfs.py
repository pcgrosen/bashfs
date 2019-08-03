import trio
import errno
import signal
import pyfuse3
import logging
import subprocess
from itertools import count


l = logging.getLogger("bashfs.bashfs")

BASHFS_ESCAPE = b"!"
BASHFS_RUN = b"run"

class Node:
    def __init__(self, parent, name, num, is_root=False):
        self.is_root = is_root
        self.parent = parent
        self.num = num
        if not self.is_root:
            if len(name) <= 0:
                raise ValueError("name must be non-empty")
            if b"/" in name:
                raise ValueError("name cannot contain banned characters")
        else:
            self.parent = self
        self.name = name
        self.translated = self.translate(name)
        self.is_last = name == BASHFS_RUN
        self.children = {}

    @staticmethod
    def translate(encoded):
        if encoded is None:
            return None
        out = ""
        iterator = iter(encoded)
        for c in iterator:
            if c == ord(b"!"):
                try:
                    n = next(iterator)
                except StopIteration:
                    raise pyfuse3.FUSEError(errno.ENOENT)
                out += chr(n ^ 0x40)
            else:
                out += chr(c)
        return out.encode("ascii")

    def make_path(self):
        if not self.is_root:
            p = self.parent.make_path()
            if self.is_last:
                return p if p else b""
            if p:
                return p + b" | " + self.translated
            else:
                return self.translated
        return None

    def __repr__(self):
        return "<Node id=%r name=%r path=%r>" % (self.num, self.name, self.make_path())

    def add_child(self, child):
        self.children[child.name] = child

class BashFS(pyfuse3.Operations):
    def __init__(self):
        super(pyfuse3.Operations, self).__init__()
        signal.signal(signal.SIGCHLD, signal.SIG_IGN)
        self._inode_generator = count(start=10)
        self._file_generator = count(start=10)
        self._inode_map = {pyfuse3.ROOT_INODE: Node(None, None,
                                                    pyfuse3.ROOT_INODE,
                                                    is_root=True)}
        self._proc_map = {}

    def _make_child_node(self, node_p, name):
        new_num = next(self._inode_generator)
        new_node = Node(node_p, name, new_num)
        node_p.add_child(new_node)
        self._inode_map[new_num] = new_node
        return new_node

    def _get_or_create_child_node(self, node_p, name):
        if name in node_p.children:
            return node_p.children[name]
        return self._make_child_node(node_p, name)

    def _get_node(self, inode):
        return self._inode_map[inode]

    async def lookup(self, inode_p, name, ctx=None):
        l.debug("lookup: inode %r, name %r", inode_p, name)
        if name == b".":
            return inode_p
        if name == b"..":
            return inode_p.parent
        node_p = self._get_node(inode_p)
        res_node = self._get_or_create_child_node(node_p, name)
        return await self.getattr(res_node.num, ctx=ctx)

    async def getattr(self, inode, ctx=None):
        node = self._get_node(inode)

        l.debug("getattr: %r", node)

        entry = pyfuse3.EntryAttributes()
        entry.st_ino = inode
        entry.generation = 0
        entry.entry_timeout = 300
        entry.attr_timeout = 300
        if not node.is_last:
            entry.st_mode = 0o040777
        else:
            entry.st_mode = 0o100777
        entry.st_nlink = 1

        entry.st_uid = 1000
        entry.st_gid = 1000
        entry.st_rdev = 0
        entry.st_size = 4096

        entry.st_blksize = 512
        entry.st_blocks = 1
        entry.st_atime_ns = 1
        entry.st_mtime_ns = 1
        entry.st_ctime_ns = 1
        return entry

    async def access(self, inode, mode, ctx):
        return True

    async def statfs(self, ctx):
        stat_ = pyfuse3.StatvfsData()

        stat_.f_bsize = 512
        stat_.f_frsize = 512

        stat_.f_blocks = 0
        stat_.f_bfree = 20
        stat_.f_bavail = 20

        thing = len(self._inode_map)
        stat_.f_files = thing
        stat_.f_ffree = thing + 2
        stat_.f_favail = thing + 2

        return stat_

    async def opendir(self, inode, ctx):
        return inode

    async def readdir(self, inode, off, token):
        l.debug("readdir: inode=%r, off=%r, token=%r", inode, off, token)
        if off < 1:
            pyfuse3.readdir_reply(token, BASHFS_RUN,
                                  await self.lookup(inode, BASHFS_RUN), 1)
        return None

    async def open(self, inode, flags, ctx):
        path = self._get_node(inode).make_path()
        l.debug("open: %r", path)
        file_handle = next(self._file_generator)
        proc = await trio.open_process(path.decode(),
                                       shell=True,
                                       stdout=subprocess.PIPE,
                                       stdin=subprocess.PIPE)
        self._proc_map[file_handle] = proc
        return file_handle

    async def read(self, file_handle, offset, length):
        p = self._proc_map[file_handle]
        return await p.stdout.receive_some(length)

    async def write(self, file_handle, offset, data):
        p = self._proc_map[file_handle]
        return await p.stdin.send_all(data)

    async def release(self, file_handle):
        if self._proc_map[file_handle].poll() is None:
            self._proc_map[file_handle].terminate()

    async def releasedir(self, inode):
        return None
