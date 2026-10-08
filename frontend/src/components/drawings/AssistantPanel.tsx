import { useCallback, useEffect, useRef, useState, type KeyboardEvent } from "react";
import { ApiError, api } from "../../lib/api";
import type { AssistantAction, AssistantAnswer, AssistantStatus } from "./types";

type ActionState = "proposed" | "applying" | "applied" | "failed" | "dismissed";

interface ShownAction extends AssistantAction {
  state: ActionState;
  error?: string;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  at: string;
  actions?: ShownAction[];
  dropped?: { kind: string | null; reason: string }[];
  needs_engineer?: boolean;
  /** The assistant could not answer: shown, never sent back as part of the conversation. */
  failed?: boolean;
}

const KEEP = 40;
const SUGGESTIONS = [
  "What still needs my attention on this system?",
  "Which floors are not approved yet, and why?",
  "What did the consultant answer last?",
  "What does the contractor still owe us?",
];

function newId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

/** The Drawings Assistant: a chat beside the page that answers from the
 *  project's records (what every tab shows, for the system on show) and
 *  proposes the changes asked for. Each proposal is the call the page's
 *  own button makes, shown with Apply: the assistant writes nothing, the
 *  engineer does. The conversation lives in this browser only. */
export function AssistantPanel({
  projectId,
  system,
  canEdit,
  onChanged,
  onOpenDrawing,
}: {
  projectId: number;
  system: string;
  canEdit: boolean;
  onChanged: () => void;
  onOpenDrawing: (id: number) => void;
}) {
  const storageKey = `drawings.chat.${projectId}.${system}`;
  const openKey = `drawings.chat.open.${projectId}`;
  const [open, setOpen] = useState<boolean>(() => {
    try {
      return localStorage.getItem(openKey) === "1";
    } catch {
      return false;
    }
  });
  const [status, setStatus] = useState<AssistantStatus | null>(null);
  // The conversation of this project and system, as this browser remembers
  // it. The page mounts the panel afresh per system (its key), so this is
  // read once per conversation.
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    try {
      const saved = localStorage.getItem(storageKey);
      return saved ? (JSON.parse(saved) as ChatMessage[]) : [];
    } catch {
      return [];
    }
  });
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const remember = useCallback(
    (next: ChatMessage[]) => {
      setMessages(next);
      try {
        localStorage.setItem(storageKey, JSON.stringify(next.slice(-KEEP)));
      } catch {
        /* storage blocked: the conversation lasts the page */
      }
    },
    [storageKey],
  );

  useEffect(() => {
    if (!open) return;
    api
      .get<AssistantStatus>(`/projects/${projectId}/drawings/assistant`)
      .then(setStatus)
      .catch((e) => setStatus({ available: false, reason: (e as Error).message, model: null, can_apply: false, actions: {} }));
  }, [open, projectId]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, busy, open]);

  const toggle = (next: boolean) => {
    setOpen(next);
    try {
      localStorage.setItem(openKey, next ? "1" : "0");
    } catch {
      /* not remembered */
    }
    if (next) window.setTimeout(() => inputRef.current?.focus(), 50);
  };

  const send = async (text: string) => {
    const message = text.trim();
    if (!message || busy) return;
    const history = messages
      .filter((m) => !m.failed)
      .slice(-12)
      .map((m) => ({ role: m.role, text: m.text }));
    const mine: ChatMessage = { id: newId(), role: "user", text: message, at: new Date().toISOString() };
    const shown = [...messages, mine];
    remember(shown);
    setDraft("");
    setBusy(true);
    try {
      const answer = await api.post<AssistantAnswer>(`/projects/${projectId}/drawings/assistant`, { system, message, history });
      remember([
        ...shown,
        {
          id: newId(),
          role: "assistant",
          text: answer.reply,
          at: new Date().toISOString(),
          actions: answer.actions.map((a) => ({ ...a, state: "proposed" as ActionState })),
          dropped: answer.dropped,
          needs_engineer: answer.needs_engineer,
        },
      ]);
    } catch (e) {
      remember([...shown, { id: newId(), role: "assistant", text: (e as Error).message, at: new Date().toISOString(), failed: true }]);
    } finally {
      setBusy(false);
      inputRef.current?.focus();
    }
  };

  const setAction = (messageId: string, index: number, patch: Partial<ShownAction>) => {
    setMessages((prev) => {
      const next = prev.map((m) =>
        m.id === messageId && m.actions ? { ...m, actions: m.actions.map((a, i) => (i === index ? { ...a, ...patch } : a)) } : m,
      );
      try {
        localStorage.setItem(storageKey, JSON.stringify(next.slice(-KEEP)));
      } catch {
        /* not remembered */
      }
      return next;
    });
  };

  /** The engineer's word: the proposal becomes the page's own call, under the engineer's role. */
  const apply = async (messageId: string, index: number, action: ShownAction) => {
    setAction(messageId, index, { state: "applying", error: undefined });
    try {
      if (action.method === "PUT") await api.put(action.path, action.body);
      else if (action.method === "PATCH") await api.patch(action.path, action.body);
      else await api.post(action.path, action.body);
      setAction(messageId, index, { state: "applied" });
      onChanged();
    } catch (e) {
      const error =
        e instanceof ApiError && e.code === "merge_review"
          ? "Both floors already carry shop drawings: review and confirm the merge on the Review & Issues tab."
          : (e as Error).message;
      setAction(messageId, index, { state: "failed", error });
    }
  };

  const clear = () => {
    if (messages.length > 0 && !window.confirm("Clear this conversation? The records are not touched.")) return;
    remember([]);
  };

  const onKey = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      void send(draft);
    }
  };

  if (!open) {
    return (
      <button
        type="button"
        onClick={() => toggle(true)}
        className="fixed bottom-6 right-6 z-40 flex items-center gap-2 rounded-full bg-navy-900 px-4 py-3 text-sm font-semibold text-white shadow-lg hover:bg-navy-950"
        aria-label="Open the Drawings Assistant"
      >
        <span aria-hidden="true">✨</span> Assistant
      </button>
    );
  }

  const unavailable = status !== null && !status.available;
  const applyAllowed = canEdit && (status?.can_apply ?? true);

  return (
    <aside
      className="fixed bottom-0 right-0 z-40 flex h-[85vh] w-full max-w-[420px] flex-col rounded-tl-2xl border border-gray-200 bg-white shadow-2xl"
      aria-label="Drawings Assistant"
    >
      <div className="flex items-start justify-between gap-3 border-b border-gray-100 px-4 py-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2 text-sm font-bold text-navy-900">
            <span aria-hidden="true">✨</span> Drawings Assistant
            <span className="rounded-full bg-brand-50 px-2 py-0.5 text-[11px] font-semibold text-brand-700">{system}</span>
          </div>
          <p className="mt-0.5 text-xs text-gray-500">
            Answers from this project's records. Changes it proposes are applied only when you say so.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <button type="button" onClick={clear} className="rounded-lg px-2 py-1 text-xs font-medium text-gray-500 hover:bg-gray-50" title="Clear the conversation">
            Clear
          </button>
          <button type="button" onClick={() => toggle(false)} className="rounded-lg px-2 py-1 text-sm text-gray-500 hover:bg-gray-50" aria-label="Close">
            ✕
          </button>
        </div>
      </div>

      {unavailable && (
        <div className="border-b border-amber-200 bg-amber-50 px-4 py-2.5 text-xs text-amber-900">
          The assistant is not available here: {status?.reason ?? "unknown reason"}
        </div>
      )}

      <div ref={listRef} className="flex-1 space-y-3 overflow-y-auto px-4 py-3">
        {messages.length === 0 && (
          <div className="space-y-2">
            <p className="text-xs text-gray-500">Ask about this system's drawings, or ask for a change. For example:</p>
            {SUGGESTIONS.map((s) => (
              <button
                key={s}
                type="button"
                disabled={busy || unavailable}
                onClick={() => void send(s)}
                className="block w-full rounded-lg border border-gray-200 px-3 py-2 text-left text-xs text-navy-900 hover:border-brand-300 hover:bg-brand-50 disabled:opacity-50"
              >
                {s}
              </button>
            ))}
            {canEdit && (
              <p className="text-[11px] text-gray-400">
                A change ("set EP-SDW-FA-001 R1 to approved", "confirm the R2 found for the 3rd floor") comes back as a proposal with Apply.
              </p>
            )}
          </div>
        )}
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={`max-w-[92%] rounded-2xl px-3.5 py-2.5 text-sm ${
                m.role === "user"
                  ? "bg-brand-600 text-white"
                  : m.failed
                    ? "border border-rose-200 bg-rose-50 text-rose-800"
                    : "border border-gray-200 bg-gray-50 text-navy-900"
              }`}
            >
              <div className="whitespace-pre-wrap">{m.text}</div>
              {m.needs_engineer && <div className="mt-1.5 text-[11px] font-medium text-amber-800">Needs your judgment: the records do not settle it.</div>}
              {m.actions && m.actions.length > 0 && (
                <ul className="mt-2 space-y-2">
                  {m.actions.map((a, i) => (
                    <li key={`${m.id}-${i}`} className="rounded-lg border border-gray-200 bg-white p-2.5">
                      <div className="text-xs font-semibold text-navy-900">{a.label}</div>
                      {(a.floor || a.reason) && (
                        <div className="mt-0.5 text-[11px] text-gray-500">
                          {a.floor && <span>{a.floor}</span>}
                          {a.floor && a.reason && " · "}
                          {a.reason}
                        </div>
                      )}
                      <div className="mt-2 flex flex-wrap items-center gap-2">
                        {a.state === "applied" && <span className="text-xs font-medium text-emerald-700">✓ Applied</span>}
                        {a.state === "dismissed" && <span className="text-xs text-gray-400">Dismissed</span>}
                        {a.state === "failed" && <span className="text-xs text-rose-700">{a.error ?? "Could not be applied"}</span>}
                        {(a.state === "proposed" || a.state === "failed" || a.state === "applying") && applyAllowed && (
                          <>
                            <button
                              type="button"
                              disabled={a.state === "applying"}
                              onClick={() => void apply(m.id, i, a)}
                              className="rounded-lg bg-brand-600 px-3 py-1 text-xs font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
                            >
                              {a.state === "applying" ? "Applying…" : a.state === "failed" ? "Try again" : "Apply"}
                            </button>
                            <button
                              type="button"
                              disabled={a.state === "applying"}
                              onClick={() => setAction(m.id, i, { state: "dismissed" })}
                              className="rounded-lg border border-gray-300 px-3 py-1 text-xs font-medium text-navy-900 hover:bg-gray-50 disabled:opacity-50"
                            >
                              Dismiss
                            </button>
                          </>
                        )}
                        {a.state === "proposed" && !applyAllowed && <span className="text-[11px] text-gray-400">Your role cannot apply changes.</span>}
                        {a.drawing_id !== null && (
                          <button type="button" onClick={() => onOpenDrawing(a.drawing_id as number)} className="text-xs font-medium text-brand-700 hover:underline">
                            Open drawing
                          </button>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
              {m.dropped && m.dropped.length > 0 && (
                <div className="mt-2 text-[11px] text-gray-500">
                  Not proposed (the records refused it): {m.dropped.map((d) => d.reason).join("; ")}
                </div>
              )}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex justify-start">
            <div className="rounded-2xl border border-gray-200 bg-gray-50 px-3.5 py-2.5 text-sm text-gray-500">Reading the project's records…</div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-100 p-3">
        <div className="flex items-end gap-2">
          <textarea
            ref={inputRef}
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onKeyDown={onKey}
            disabled={busy || unavailable}
            rows={2}
            placeholder={unavailable ? "The assistant is not available on this project" : `Ask about ${system}, or ask for a change…`}
            className="min-h-[44px] flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none disabled:bg-gray-50"
          />
          <button
            type="button"
            disabled={busy || unavailable || !draft.trim()}
            onClick={() => void send(draft)}
            className="rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50"
          >
            Send
          </button>
        </div>
        <p className="mt-1.5 text-[11px] text-gray-400">Enter sends, Shift+Enter for a new line. The conversation stays in this browser.</p>
      </div>
    </aside>
  );
}
