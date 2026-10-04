import { useEffect, useState } from "react";
import { ApiError, api } from "../lib/api";

interface MaterialRequest {
  to: string;
  subject: string;
  body: string;
  to_confirm: string[];
  not_in_schedule: string[];
  els_in_scope: boolean;
  model: string;
  from_cache: boolean;
}

/** The Request Material email for a sample board not yet sent: drafted by
 * the AI from the project's Schedules of Material, checked by the platform,
 * and edited and sent by the engineer. Nothing is sent from here. */
export function RequestMaterialDialog({ projectId, onClose }: { projectId: number; onClose: () => void }) {
  const [draft, setDraft] = useState<MaterialRequest | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [to, setTo] = useState("");
  const [subject, setSubject] = useState("");
  const [body, setBody] = useState("");
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    let live = true;
    api
      .post<MaterialRequest>(`/projects/${projectId}/samples/request-material`)
      .then((d) => {
        if (!live) return;
        setDraft(d);
        setTo(d.to);
        setSubject(d.subject);
        setBody(d.body);
      })
      .catch((e) => live && setError(e instanceof ApiError ? e.message : "The email could not be drafted"));
    return () => {
      live = false;
    };
  }, [projectId]);

  const mailto = `mailto:${encodeURIComponent(to)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(`To: ${to}\nSubject: ${subject}\n\n${body}`);
      setCopied(true);
    } catch {
      setError("The browser did not allow copying: select the text and copy it.");
    }
  };

  return (
    <div role="dialog" aria-modal="true" aria-label="Request material" className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4">
      <div className="flex max-h-[92vh] w-full max-w-3xl flex-col overflow-hidden rounded-xl bg-white shadow-xl">
        <div className="flex items-start justify-between gap-3 border-b border-gray-200 px-5 py-3">
          <div>
            <h2 className="text-base font-semibold">Request material for the sample board</h2>
            <p className="text-xs text-gray-500">Drafted from the Schedules of Material. Check it, edit it, and send it from your mail — nothing is sent from here.</p>
          </div>
          <button type="button" onClick={onClose} aria-label="Close" className="text-gray-500 hover:text-gray-800">
            ✕
          </button>
        </div>
        <div className="space-y-3 overflow-y-auto px-5 py-4 text-sm">
          {error && <div role="alert" className="rounded-lg bg-red-50 p-3 text-red-700">{error}</div>}
          {!draft && !error && <p className="text-gray-500">Drafting the email from the schedules…</p>}
          {draft && (
            <>
              {(draft.not_in_schedule.length > 0 || draft.to_confirm.length > 0 || !draft.els_in_scope) && (
                <div className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-amber-900">
                  <div className="font-semibold">Check before sending</div>
                  <ul className="mt-1 list-disc space-y-0.5 pl-5">
                    {draft.not_in_schedule.map((line) => (
                      <li key={`n-${line}`}>
                        <span className="font-medium">Not in the schedules:</span> {line}
                      </li>
                    ))}
                    {draft.to_confirm.map((line) => (
                      <li key={`c-${line}`}>{line}</li>
                    ))}
                    {!draft.els_in_scope && <li>Emergency lighting is not a system of this project: the EML lines have no schedule.</li>}
                  </ul>
                </div>
              )}
              <label className="block">
                <span className="text-gray-700">To</span>
                <input value={to} onChange={(e) => setTo(e.target.value)} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5" />
              </label>
              <label className="block">
                <span className="text-gray-700">Subject</span>
                <input value={subject} onChange={(e) => setSubject(e.target.value)} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-1.5" />
              </label>
              <label className="block">
                <span className="text-gray-700">Message</span>
                <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={20} className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 font-mono text-xs leading-relaxed" />
              </label>
              <p className="text-xs text-gray-400">
                {draft.from_cache ? "Reused: the schedules have not changed since the last draft." : `Drafted by ${draft.model || "the AI"}.`}
              </p>
            </>
          )}
        </div>
        <div className="flex flex-wrap justify-end gap-2 border-t border-gray-200 px-5 py-3">
          <button type="button" onClick={onClose} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50">
            Close
          </button>
          <button type="button" disabled={!draft} onClick={copy} className="rounded-lg border border-gray-300 px-4 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-50">
            {copied ? "Copied" : "Copy"}
          </button>
          <a
            href={draft ? mailto : undefined}
            aria-disabled={!draft}
            className={`rounded-lg px-4 py-2 text-sm font-semibold text-white ${draft ? "bg-brand-600 hover:bg-brand-700" : "pointer-events-none bg-gray-300"}`}
          >
            Open in email
          </a>
        </div>
      </div>
    </div>
  );
}
