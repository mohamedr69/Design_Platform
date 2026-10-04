/** Drawings > Assign Draftsman: the ten things a draftsman is handed before
 * the shop drawings start, whether each is ready, and the email that hands
 * the project over (app.services.draftsman_assignment).
 *
 * An item that is not received or not ready is highlighted until it is ready
 * or the engineer skips it. The project is assigned once every item is one or
 * the other: the button downloads an Outlook draft -- To the draftsman, the
 * letter with each item's status and the drawings received log, the
 * schedules attached -- to check and send. Every assignment is logged. */
import { useCallback, useEffect, useState } from "react";

import { ApiError, api } from "../../lib/api";

type ItemState = "ready" | "missing" | "skipped";

interface AssignItem {
  key: string;
  n: number;
  name: string;
  detail: string;
  manual: boolean;
  state: ItemState;
  ready: boolean;
  reason: string;
}

interface LogEntry {
  at: string;
  by: string;
  name: string;
  email: string;
  items: { key: string; name: string; state: ItemState; reason: string }[];
  files: string[];
  notes: string[];
}

interface Assignment {
  items: AssignItem[];
  ready: boolean;
  draftsman: { name: string; email: string };
  known: { name: string; email: string }[];
  log: LogEntry[];
}

const CHIP: Record<ItemState, { label: string; className: string }> = {
  ready: { label: "Ready", className: "bg-green-50 text-green-700 ring-green-200" },
  missing: { label: "Not ready", className: "bg-red-50 text-red-700 ring-red-200" },
  skipped: { label: "Skipped", className: "bg-gray-100 text-gray-500 ring-gray-200" },
};

function when(value: string): string {
  const date = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(value) ? value : `${value}Z`);
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function AssignDraftsmanTab({ projectId, canEdit }: { projectId: number; canEdit: boolean }) {
  const [data, setData] = useState<Assignment | null>(null);
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const body = await api.get<Assignment>(`/projects/${projectId}/draftsman`);
      setData(body);
      setName((was) => was || body.draftsman.name);
      setEmail((was) => was || body.draftsman.email);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The checklist could not be loaded");
    }
  }, [projectId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function act(item: AssignItem, action: "skip" | "unskip" | "ready" | "not_ready") {
    setBusy(item.key);
    setError(null);
    try {
      setData(await api.put<Assignment>(`/projects/${projectId}/draftsman/items/${item.key}`, { action }));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "It could not be saved");
    } finally {
      setBusy(null);
    }
  }

  async function assign() {
    setBusy("assign");
    setError(null);
    setDone(null);
    try {
      await api.download(`/projects/${projectId}/draftsman/assign`, "Shop drawings assignment.eml", {
        name: name.trim(),
        email: email.trim(),
      });
      setDone(
        `The email to ${name.trim()} is downloaded: open it -- it opens in Outlook as a draft with the files attached -- check it and press Send.`,
      );
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "The assignment could not be made");
    } finally {
      setBusy(null);
    }
  }

  if (!data) {
    return <p className="mt-4 text-sm text-gray-400">{error ?? "Checking the items..."}</p>;
  }
  const missing = data.items.filter((i) => i.state === "missing");
  const pick = (value: string) => {
    const known = data.known.find((k) => k.email.toLowerCase() === value.toLowerCase() || k.name === value);
    if (known) {
      setName(known.name);
      setEmail(known.email);
    }
  };

  return (
    <div className="mt-4 space-y-4">
      <section className="rounded-xl border border-gray-200 bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="max-w-2xl">
            <h2 className="text-sm font-bold text-navy-900">Assign the shop drawings to a draftsman</h2>
            <p className="mt-1 text-sm text-gray-600">
              The draftsman is handed the ten items below. Each is checked here; one not received or not ready is
              highlighted until it is ready or you skip it. Assigning downloads the email as an Outlook draft — the letter,
              each item&rsquo;s status, the drawings received log and the schedules attached — to check and send.
            </p>
          </div>
          {canEdit && (
            <div className="flex flex-wrap items-end gap-2">
              <label className="text-xs text-gray-500">
                Draftsman
                <input
                  list="draftsmen"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    pick(e.target.value);
                  }}
                  className="mt-1 block w-40 rounded-lg border border-gray-300 px-2 py-1.5 text-sm text-navy-900"
                />
              </label>
              <label className="text-xs text-gray-500">
                Email
                <input
                  list="draftsman-emails"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    pick(e.target.value);
                  }}
                  className="mt-1 block w-60 rounded-lg border border-gray-300 px-2 py-1.5 text-sm text-navy-900"
                />
              </label>
              <datalist id="draftsmen">
                {data.known.map((k) => (
                  <option key={k.email} value={k.name} />
                ))}
              </datalist>
              <datalist id="draftsman-emails">
                {data.known.map((k) => (
                  <option key={k.email} value={k.email} />
                ))}
              </datalist>
              <button
                onClick={() => void assign()}
                disabled={!data.ready || busy !== null || !name.trim() || !email.trim()}
                title={data.ready ? "Make the email to the draftsman" : "Every item must be ready or skipped first"}
                className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
              >
                {busy === "assign" ? "Preparing the email..." : "Assign draftsman"}
              </button>
            </div>
          )}
        </div>
        {!data.ready && (
          <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">
            {missing.length} item{missing.length === 1 ? " is" : "s are"} not ready:{" "}
            {missing.map((i) => `${i.n}. ${i.name}`).join(", ")}. Prepare {missing.length === 1 ? "it" : "them"} or skip
            {missing.length === 1 ? " it" : " them"} to assign.
          </p>
        )}
        {error && <p className="mt-3 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-800">{error}</p>}
        {done && <p className="mt-3 rounded-lg bg-green-50 px-3 py-2 text-sm text-green-800">{done}</p>}
      </section>

      <section className="overflow-hidden rounded-xl border border-gray-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="border-b border-gray-200 bg-gray-50 text-left text-xs uppercase tracking-wide text-gray-500">
            <tr>
              <th className="w-10 px-4 py-2.5">#</th>
              <th className="px-4 py-2.5">Item</th>
              <th className="px-4 py-2.5">Status</th>
              <th className="px-4 py-2.5">Where it stands</th>
              {canEdit && <th className="px-4 py-2.5 text-right">Actions</th>}
            </tr>
          </thead>
          <tbody>
            {data.items.map((item) => (
              <tr
                key={item.key}
                className={`border-t border-gray-100 align-top ${item.state === "missing" ? "bg-red-50/60" : ""}`}
              >
                <td className="px-4 py-3 tabular-nums text-gray-500">{item.n}</td>
                <td className="px-4 py-3">
                  <div className="font-semibold text-navy-900">{item.name}</div>
                  <div className="mt-0.5 max-w-md text-xs text-gray-500">{item.detail}</div>
                </td>
                <td className="px-4 py-3">
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ${CHIP[item.state].className}`}>
                    {CHIP[item.state].label}
                  </span>
                  {item.manual && <div className="mt-1 text-[11px] text-gray-400">marked by the engineer</div>}
                </td>
                <td className={`px-4 py-3 text-xs ${item.state === "missing" ? "text-red-800" : "text-gray-600"}`}>
                  {item.reason}
                  {item.state === "skipped" && !item.ready && <span className="text-gray-400"> (skipped)</span>}
                </td>
                {canEdit && (
                  <td className="whitespace-nowrap px-4 py-3 text-right text-xs">
                    {item.manual && item.state !== "skipped" && (
                      <button
                        onClick={() => void act(item, item.ready ? "not_ready" : "ready")}
                        disabled={busy !== null}
                        className="mr-2 rounded border border-gray-300 px-2 py-1 font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        {item.ready ? "Not ready" : "Mark ready"}
                      </button>
                    )}
                    <button
                      onClick={() => void act(item, item.state === "skipped" ? "unskip" : "skip")}
                      disabled={busy !== null}
                      className="rounded border border-gray-300 px-2 py-1 font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                    >
                      {item.state === "skipped" ? "Unskip" : "Skip"}
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="rounded-xl border border-gray-200 bg-white p-5">
        <h3 className="text-sm font-bold text-navy-900">Assignment log</h3>
        {data.log.length === 0 ? (
          <p className="mt-2 text-sm text-gray-400">Not assigned yet.</p>
        ) : (
          <ul className="mt-3 space-y-3">
            {data.log.map((entry, i) => (
              <li key={i} className="rounded-lg border border-gray-100 p-3 text-sm">
                <div className="flex flex-wrap items-baseline justify-between gap-2">
                  <span className="font-semibold text-navy-900">
                    {entry.name} <span className="font-normal text-gray-500">({entry.email})</span>
                  </span>
                  <span className="text-xs text-gray-500">
                    {when(entry.at)} · by {entry.by}
                  </span>
                </div>
                <div className="mt-1 flex flex-wrap gap-1.5">
                  {entry.items.map((it) => (
                    <span
                      key={it.key}
                      title={it.reason}
                      className={`rounded-full px-2 py-0.5 text-[11px] ring-1 ${CHIP[it.state].className}`}
                    >
                      {it.name}
                    </span>
                  ))}
                </div>
                {entry.files.length > 0 && (
                  <div className="mt-1 text-xs text-gray-500">Attached: {entry.files.join(", ")}</div>
                )}
                {entry.notes.length > 0 && <div className="mt-0.5 text-xs text-amber-700">{entry.notes.join("; ")}</div>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
