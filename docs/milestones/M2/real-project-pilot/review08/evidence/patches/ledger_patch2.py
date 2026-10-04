"""M2 review 08 (R8-03): concurrent first opens of a ledger file set up the schema and the scope in one immediate transaction."""
import pathlib

p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/ledger.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('''        with self._connect() as con:
            con.executescript("""''', '''        with self._connect() as con:
            # schema, column upgrade and scope creation are one immediate transaction: of several handles opening the
            # file at once (threads or processes), one creates and records its limits; the others wait for the lock and
            # are then compared with them like any later handle
            con.execute("begin immediate")
            for statement in """''')
sub('''                    authorized_by text, reason text, pid integer);
            """)
            columns''', '''                    authorized_by text, reason text, pid integer)
            """.split(";"):
                con.execute(statement)
            columns''')
sub('''            # created atomically: of two handles creating the scope at once, one records its limits and the other is
            # then compared with them like any later handle
            con.execute("begin immediate")
            row = con.execute''', '''            row = con.execute''')
sub('''    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        con.execute("pragma journal_mode=wal")
        return con''', '''    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        # switching the journal mode takes an exclusive lock and does not wait on the busy handler, so it is done once
        # (WAL persists in the file) and retried while another handle holds the file
        deadline = time.monotonic() + 30
        while con.execute("pragma journal_mode").fetchone()[0].lower() != "wal":
            try:
                con.execute("pragma journal_mode=wal")
            except sqlite3.OperationalError:
                if time.monotonic() > deadline:
                    raise
                time.sleep(0.02)
        return con''')
p.write_text(s, encoding="utf-8", newline="\n")
print("ok")
