"""ORCH-08C task item 6 (R39-09, Q1): read-only inspection of the INSTALLED Claude Code CLI file. The CLI is never
executed: the file is opened for reading and searched for byte strings of its embedded JavaScript bundle. Writes one
JSON file (argv[1]) with the file's path, size and sha256 and, per finding, the byte offset of a short fragment, the
fragment itself (kept short) and the sha256 of a fixed 2 KiB window around it, so anyone can re-locate it.
Usage: model_id_evidence_r39.py <out json>"""
import hashlib
import json
import pathlib
import re
import shutil
import sys

CANDIDATES = [pathlib.Path("C:/Users/moham/AppData/Local/Microsoft/WinGet/Packages/Anthropic.ClaudeCode_Microsoft.Winget.Source_8wekyb3d8bbwe/claude.exe")]
FINDINGS = [
    ("package_and_version", re.compile(rb"@anthropic-ai/claude-code.{1,160}?2\.1\.263.{1,200}?20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ.{0,48}", re.S), 400,
     "the embedded package name, followed by its version string, build time and source commit"),
    ("version_banner", rb"// Version: 2.1.263", 0, "a bundle chunk header naming the version"),
    ("catalog_entry_sonnet5", rb'{id:"claude-sonnet-5",family:"sonnet"', 0, "the baked model catalog entry claude-sonnet-5"),
    ("catalog_first_party_sonnet5", rb'provider_ids:{first_party:"claude-sonnet-5"', 0, "its first-party wire id"),
    ("catalog_entry_opus5", rb'{id:"claude-opus-5",family:"opus"', 0, "the baked model catalog entry claude-opus-5"),
    ("catalog_first_party_opus5", rb'provider_ids:{first_party:"claude-opus-5"', 0, "its first-party wire id"),
    ("alias_opus", rb'aliases:{opus:{default:"claude-opus-5"', 0, "alias opus -> claude-opus-5 (first party default)"),
    ("alias_sonnet", rb'sonnet:{default:"claude-sonnet-5",per_provider:', 0, "alias sonnet -> claude-sonnet-5 (first party default; per-provider overrides follow)"),
    ("recognized_ids", rb'"claude-opus-5","claude-sonnet-4-0","claude-sonnet-4-5","claude-sonnet-4-6","claude-sonnet-5"]', 0,
     "the list of recognized model ids (includes claude-opus-5 and claude-sonnet-5)"),
    ("alias_list", rb'["sonnet","opus","haiku","fable","best","sonnet[1m]","opus[1m]","fable[1m]","opusplan"]', 0, "the alias names"),
    ("parse_user_model", rb"function wt(e){let t=e.trim(),r=t.toLowerCase()", 0,
     "parseUserSpecifiedModel: aliases resolve through the default-model getters; any other value is returned through uS"),
    ("identity_passthrough", rb"function uS(e){return e}", 0, "uS is the identity: a full id passes unchanged"),
    ("sonnet_default_getter", rb"function Lp(){let e=a.ANTHROPIC_DEFAULT_SONNET_MODEL", 0,
     "the sonnet alias honours ANTHROPIC_DEFAULT_SONNET_MODEL, else the catalog alias"),
    ("vet_user_model", rb"function DAt(e){if(e&&!Cr(e))return Xh(e)??void 0", 0,
     "vetUserSpecifiedModel: a model outside an org allowlist steps down or is dropped"),
    ("export_names", rb"wt as parseUserSpecifiedModel", 0, "the export mapping of the minified names"),
    ("ledger_record_cost", rb"recordCost(e,t,o){this.#l[o]=t", 0, "the cost ledger's per-model usage map is keyed by the third argument"),
    ("usage_entry_fields", rb"o.canonicalModel=Fe(r),o.provider=El(r)", 0, "each usage entry also carries canonicalModel and provider"),
    ("usage_keyed_by_request_model", rb"Ib+=VG($N(F,Oc),Oc,f.model,f.querySource", 0,
     "the streaming path records usage under f.model (the request's model), not the response's message.model"),
    ("refusal_fallback_key", rb"lWe=Em?f.serverRefusalFallback?.model??f.model:f.model", 0,
     "after a server refusal fallback the usage key is the fallback model"),
    ("result_model_usage", rb"total_cost_usd:ru(),usage:Ai(),modelUsage:jw()", 0, "the JSON result's modelUsage is the cost ledger's map"),
    ("catalog_url", rb"https://downloads.claude.ai/model-catalog/v1/catalog.json", 0, "a signed remote model catalog the CLI can load"),
]


def main(argv):
    path = next((p for p in CANDIDATES if p.is_file()), None)
    which = shutil.which("claude")
    if path is None:
        raise SystemExit("the installed CLI file was not found")
    data = path.read_bytes()
    out = {"cli_file": path.as_posix(), "on_path": which, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
           "executed": False, "method": "read-only byte search of the installed file; the CLI was not executed", "findings": {}}
    for name, needle, extra, what in FINDINGS:
        pat = needle if isinstance(needle, re.Pattern) else re.compile(re.escape(needle))
        hits = [m.start() for m in pat.finditer(data)]
        rec = {"what": what, "needle": pat.pattern.decode("utf-8", "replace"), "occurrences": len(hits), "offsets": hits[:5]}
        if hits:
            i = hits[0]
            w = data[max(0, i - 1024): i + 1024]
            rec["window_2k_sha256"] = hashlib.sha256(w).hexdigest()
            if extra:
                rec["following_text"] = re.sub(r"[^\x20-\x7e]+", " ", data[i: i + extra].decode("utf-8", "replace"))[:240]
        out["findings"][name] = rec
    v = out["findings"]["package_and_version"].get("following_text", "")
    m = re.search(r"(\d+\.\d+\.\d+)", v)
    out["embedded_version"] = m.group(1) if m else None
    b = re.search(r"(20\d\d-\d\d-\d\dT\d\d:\d\d:\d\dZ)", v)
    out["embedded_build_time"] = b.group(1) if b else None
    pathlib.Path(argv[1]).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("cli_file", "bytes", "sha256", "embedded_version", "embedded_build_time")}))
    print(json.dumps({k: v["occurrences"] for k, v in out["findings"].items()}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
