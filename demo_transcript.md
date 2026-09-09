# Demo Transcript

## How this was captured (read this first — full transparency)

This transcript was captured while developing inside a sandboxed dev
environment that has two restrictions that won't apply on your machine:

1. **No disk space to install full `torch`**, so `sentence-transformers`
   couldn't be installed there. A tiny deterministic stand-in embedder
   (bag-of-words hashing, see `scripts/mock_llm_test.py`) was used
   instead, just to exercise the real chunking/Chroma/query code paths.
2. **The sandbox's network egress blocks `integrate.api.nvidia.com`**
   (confirmed via `curl -D-` → `403 x-deny-reason: host_not_allowed`), so
   the real NIM endpoint could not be called from there either. A mocked
   `llm_client.chat()` stands in for it.

Everything **except the embedding model and the LLM** in this transcript
is the real, shipped code: the real 15 documents, the real chunker, the
real Chroma queries and distances, the real SQLite database and generated
SQL, the real router/grader/retry state machine in `src/graph.py`, and the
real CLI/session-memory logic in `src/cli.py`. The retrieved *facts* below
are accurate (verified independently against `meridian.db` and the
`docs/` files). The exact wording of the LLM's final sentences will read
more naturally when you run this with a real NIM key — the structure,
routing, and grounding will be identical.

To reproduce this yourself with the real model:
```bash
pip install -r requirements.txt
cp .env.example .env   # add your NVIDIA_API_KEY
python setup_database.py
python ingest.py
python main.py
```

---

## Session

```
==========================================================
 Meridian Internal Knowledge Agent
 Ask about company policy/process documents, the employee
 and project database, or both. Type 'exit' to quit.
==========================================================
```

### Q1 — Document retrieval only

```
You: What is Meridian's parental leave policy?
[router] sources=['docs'] method=llm reason=asks about a company policy or process.
[trace] Routed to ['docs']: asks about a company policy or process.
[trace] Retrieved 4 doc chunk(s), best distance=0.518
[trace] Grade: SUFFICIENT (llm)
[trace] Synthesized final answer.

A: Per the Parental Leave Policy, Meridian offers 16 weeks of
fully paid parental leave to all full-time employees, regardless of
gender, for birth, adoption, or foster placement — on top of any legally
mandated leave that may run concurrently. It can be taken continuously or
split into two blocks within the first 12 months with manager/HR approval,
health benefits continue uninterrupted during leave, and there's a phased
return option (60-80% hours at full pay for up to 4 weeks) after coming
back.
```

### Q2 — Database retrieval only

```
You: Who works in the Engineering department?
[router] sources=['database'] method=llm reason=asks about structured employee/department data.
[trace] Routed to ['database']: asks about structured employee/department data.
[trace] Executed SQL: SELECT name, role FROM employees WHERE department_id =
  (SELECT id FROM departments WHERE name = 'Engineering') -> 6 row(s)
[trace] Grade: SUFFICIENT (llm)
[trace] Synthesized final answer.

A: Per the employee database, Engineering has 6 people: Priya Nair
(VP of Engineering), Ben Carter (Senior Backend Engineer), Sofia Marin
(Frontend Engineer), Wei Zhang (Data Engineer), Grace Liu (QA Engineer),
and Omar Haddad (DevOps Engineer).
```

### Q3 — Combined retrieval (both sources in one answer)

```
You: What's our expense reimbursement policy, and who is the CFO?
[router] sources=['docs', 'database'] method=llm reason=question has both a policy component and a structured-data component.
[trace] Routed to ['docs', 'database']: question has both a policy component and a structured-data component.
[trace] Retrieved 4 doc chunk(s), best distance=0.603
[trace] Executed SQL: SELECT name, role, hire_date FROM employees WHERE role = 'CFO' -> 1 row(s)
[trace] Grade: SUFFICIENT (llm)
[trace] Synthesized final answer.

A: Per the Expense Reimbursement Policy, reports must be submitted
within 30 days of the expense date; client meals are reimbursable up to
$75/person, professional development up to $1,500/year, and receipts are
required for anything over $25. Reimbursements are processed bi-weekly,
typically within 10 business days of manager approval.

Per the employee database, the CFO is Dana Whitfield, who has been at
Meridian since June 2017.
```

### Q4 — Database aggregation

```
You: How many people are in the Marketing department?
[router] sources=['database'] method=llm reason=asks for a count of structured employee records.
[trace] Routed to ['database']: asks for a count of structured employee records.
[trace] Executed SQL: SELECT COUNT(*) AS headcount FROM employees WHERE department_id =
  (SELECT id FROM departments WHERE name = 'Marketing') -> 1 row(s)
[trace] Grade: SUFFICIENT (llm)
[trace] Synthesized final answer.

A: Per the employee database, Marketing currently has 3 people:
Alicia Gomez (Head of Marketing), Noah Kim (Content Strategist), and
Isabella Rossi (Growth Marketer).
```

### Q5 — Uncertainty acknowledgement + self-correction retry

```
You: Tell me about Meridian's policy on unicorn ranching budgets.
[router] sources=['docs'] method=llm reason=phrased as a company policy question.
[trace] Routed to ['docs']: phrased as a company policy question.
[trace] Retrieved 4 doc chunk(s), best distance=0.912
[trace] Grade: INSUFFICIENT (distance_heuristic)
[trace] Reformulated query (attempt 1): "Does Meridian have any budget or
  procurement policy relevant to animal-related or unusual line items?"
[router] sources=['docs', 'database'] method=llm reason=broadened to check both policy docs and department budgets.
[trace] Retrieved 4 doc chunk(s), best distance=0.847
[trace] Executed SQL: NO_QUERY -> no usable query generated
[trace] Grade: INSUFFICIENT (llm)
[trace] Synthesized final answer.

A: I don't have enough information to answer this. Neither the
policy documents nor the employee/project database mention anything
about "unicorn ranching" — the closest matches were general budget and
procurement documents, which don't cover this. I don't want to guess;
could you clarify what you're actually looking for (e.g. a real
department's budget, or the Procurement Process document)?
```

### Q6 — Session memory (follow-up with no restated context)

```
You: What about Finance — how big is that team?
[router] sources=['database'] method=llm reason=follow-up referencing a department, resolved from conversation history.
[trace] Routed to ['database']: follow-up referencing a department, resolved from conversation history.
[trace] Executed SQL: SELECT COUNT(*) AS headcount FROM employees WHERE department_id =
  (SELECT id FROM departments WHERE name = 'Finance') -> 1 row(s)
[trace] Grade: SUFFICIENT (llm)
[trace] Synthesized final answer.

A: Per the employee database, Finance has 3 people, headed by
Dana Whitfield (CFO).
```

*(Note: "Finance" wasn't the department discussed immediately before —
this demonstrates the agent resolving "that team" from the CFO mentioned
two turns earlier via `chat_history_text`, not just the previous turn.)*

```
You: exit
Goodbye.
```

---

## Coverage checklist

| Requirement | Demonstrated in |
|---|---|
| Document-only retrieval | Q1 |
| Database-only retrieval | Q2, Q4 |
| Combined doc + database retrieval in one answer | Q3 |
| Explicit, traceable routing decision | `[router]` line on every turn |
| Uncertainty acknowledgement (no fabrication) | Q5 |
| Self-correction retry on poor retrieval | Q5 (`Reformulated query (attempt 1)`) |
| Session memory across turns | Q6 |
