import pathlib
p = pathlib.Path(r"C:/t/iso/ep-platform/backend/app/ai/evidence_reader.py")
s = p.read_text(encoding="utf-8")
def sub(old, new):
    global s
    assert s.count(old) == 1, old[:60]
    s = s.replace(old, new)
sub('''                         "cost": cost if self.budget.limits.priced else None})
        if not response.ok:''', '''                         "cost": cost if self.budget.limits.priced else None})
        self._usage(task, response, cost, escalated=tier == "standard")
        if not response.ok:''')
sub('''# --- validation policy ---''', '''    def _usage(self, task: str, response, cost: float, *, escalated: bool) -> None:
        """The application's own per-call record (AiUsage), beside the run's log. Unknown price: cost 0 in the
        table, reported as unknown (None) in the run log -- never as zero cost."""
        from app.models import AiUsage

        usage = response.usage
        self.db.add(AiUsage(project_id=self.project_id, run_id=None, task=("evidence:" + task)[:32], model=(response.model or "unknown")[:64],
                            input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
                            cached_input_tokens=usage.cached_input_tokens, reasoning_tokens=usage.reasoning_tokens,
                            estimated_cost=cost if self.budget.limits.priced else 0, latency_ms=response.latency_ms or 0,
                            cache_hit=False, escalated=escalated, outcome=(response.error or "ok")[:24]))


# --- validation policy ---''')
sub('''                          schema=DISCOVER_SCHEMA)''', '''                          schema=DISCOVER_SCHEMA, max_output=800)''')
sub('''             reason: str = "", max_output: int = 900)''', '''             reason: str = "", max_output: int = 800)''')
p.write_text(s, encoding="utf-8")
print("ok")
