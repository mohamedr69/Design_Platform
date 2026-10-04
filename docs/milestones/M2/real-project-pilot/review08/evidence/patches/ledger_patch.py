"""M2 review 08 (R8-03): the persisted scope policy is authoritative."""
import pathlib

p = pathlib.Path(r"C:\t\iso\ep-platform\backend\app\ai\ledger.py")
s = p.read_text(encoding="utf-8")


def sub(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new)


sub('LEDGER_VERSION = "ai-ledger-2026-09-29.1"', 'LEDGER_VERSION = "ai-ledger-2026-09-29.2"   # .2: the persisted scope policy is authoritative (review 08)')
sub('''* **Money:** no price is assumed. Cost stays unknown unless the owner configures trustworthy prices.
"""''', '''* **Money:** no price is assumed. Cost stays unknown unless the owner configures trustworthy prices.

**The scope's persisted limits are its policy** (M2 review 08, R8-03). The first handle to open a scope records its
limits; every later handle -- another worker, another process, a restart -- is held to them:
  * a handle that supplies a limit whose value differs from the stored one -- looser *or stricter* -- is refused
    (`LedgerConfigMismatch`): a second, unrecorded policy per handle is exactly what must not happen;
  * a handle that supplies only some limits (a partial dictionary) is accepted when every supplied value equals the
    stored one; the others come from the scope; a handle that supplies none uses the scope's;
  * reservation and settlement read the effective limits from the database inside their transaction, never from
    the handle's memory;
  * the only way to change a scope's limits is `amend_limits(new, authorized_by=..., reason=...)`: explicit,
    versioned (`limits_version`), recorded in `limit_amendments` with who, why, old and new. A handle opened on the
    earlier version is refused afterwards (its limits no longer match). An amendment does not re-open a tripped
    breaker.
"""''')
sub('''class LedgerRefused(Exception):''', '''class LedgerConfigMismatch(Exception):
    """A handle's limits differ from the scope's persisted policy."""

    def __init__(self, scope: str, differences: dict) -> None:
        super().__init__(f"ledger scope {scope!r}: the supplied limits differ from its persisted policy {differences}; "
                         "use the stored policy, or amend it explicitly (Ledger.amend_limits)")
        self.scope = scope
        self.differences = differences


class LedgerRefused(Exception):''')
old_init = s[s.index("    def __post_init__(self) -> None:"):s.index("    def _connect(self) -> sqlite3.Connection:")]
new_init = '''    def __post_init__(self) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(self.path)), exist_ok=True)
        supplied = self.limits.as_dict()
        with self._connect() as con:
            con.executescript("""
                create table if not exists scopes (scope text primary key, limits text, created_at real, breaker text);
                create table if not exists entries (
                    id integer primary key autoincrement, scope text, at real, task text, adapter text, model text,
                    state text, est_in integer, est_out integer, act_in integer, act_out integer, cached_in integer,
                    turns integer, latency_ms integer, outcome text, usage_unknown integer default 0, pid integer, note text);
                create index if not exists entries_scope on entries(scope);
                create table if not exists limit_amendments (
                    id integer primary key autoincrement, scope text, at real, version integer, old text, new text,
                    authorized_by text, reason text, pid integer);
            """)
            columns = {r[1] for r in con.execute("pragma table_info(scopes)")}
            if "limits_version" not in columns:
                con.execute("alter table scopes add column limits_version integer default 1")
            # created atomically: of two handles creating the scope at once, one records its limits and the other is
            # then compared with them like any later handle
            con.execute("begin immediate")
            row = con.execute("select limits from scopes where scope = ?", (self.scope,)).fetchone()
            if row is None:
                con.execute("insert into scopes (scope, limits, created_at, breaker, limits_version) values (?, ?, ?, null, 1)",
                            (self.scope, json.dumps(supplied, sort_keys=True), time.time()))
                stored = supplied
            else:
                stored = json.loads(row[0])
            con.execute("commit")
        differences = {k: {"supplied": v, "stored": stored.get(k)} for k, v in supplied.items() if stored.get(k) != v}
        if differences:
            raise LedgerConfigMismatch(self.scope, differences)
        self.limits = Limits(**stored)

    def effective_limits(self, con=None) -> Limits:
        """The scope's persisted policy -- what reservation and settlement enforce."""
        if con is None:
            with self._connect() as c:
                return self.effective_limits(c)
        return Limits(**json.loads(con.execute("select limits from scopes where scope = ?", (self.scope,)).fetchone()[0]))

    def amend_limits(self, new: "Limits | dict", *, authorized_by: str, reason: str) -> dict:
        """Change the scope's policy explicitly: versioned and recorded (who, why, old, new). Nothing else changes it."""
        if not str(authorized_by or "").strip() or not str(reason or "").strip():
            raise ValueError("a limit amendment needs who authorised it and why")
        new = new if isinstance(new, Limits) else Limits(**new)
        with self._lock, self._connect() as con:
            con.execute("begin immediate")
            old, version = con.execute("select limits, coalesce(limits_version, 1) from scopes where scope = ?", (self.scope,)).fetchone()
            con.execute("update scopes set limits = ?, limits_version = ? where scope = ?",
                        (json.dumps(new.as_dict(), sort_keys=True), version + 1, self.scope))
            con.execute("insert into limit_amendments (scope, at, version, old, new, authorized_by, reason, pid) values (?, ?, ?, ?, ?, ?, ?, ?)",
                        (self.scope, time.time(), version + 1, old, json.dumps(new.as_dict(), sort_keys=True), authorized_by, reason, os.getpid()))
            con.execute("commit")
        self.limits = new
        return {"version": version + 1, "old": json.loads(old), "new": new.as_dict()}

    def amendments(self) -> list[dict]:
        with self._connect() as con:
            con.row_factory = sqlite3.Row
            return [dict(r) for r in con.execute("select * from limit_amendments where scope = ? order by id", (self.scope,))]

'''
s = s.replace(old_init, new_init)
sub('''        """Atomically reserve a request, or raise LedgerRefused (and record the refusal)."""
        L = self.limits
        with self._lock, self._connect() as con:
            con.execute("begin immediate")
            t = self._totals(con)''', '''        """Atomically reserve a request, or raise LedgerRefused (and record the refusal). The limits are the scope's
        persisted policy, read inside the transaction."""
        with self._lock, self._connect() as con:
            con.execute("begin immediate")
            L = self.effective_limits(con)
            t = self._totals(con)''')
sub('''        (per-request actual over a per-request cap, or an aggregate cap passed) and opens the breaker."""
        L = self.limits
        with self._lock, self._connect() as con:
            con.execute("begin immediate")''', '''        (per-request actual over a per-request cap, or an aggregate cap passed) and opens the breaker. The limits are the
        scope's persisted policy, read inside the transaction."""
        with self._lock, self._connect() as con:
            con.execute("begin immediate")
            L = self.effective_limits(con)''')
p.write_text(s, encoding="utf-8")
print("ok")
