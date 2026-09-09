# AI Prompt Log

This is the log of the key prompts used with the coding agent (Claude) to
build this project, in the order they were given. Minor clarifying
back-and-forth is summarized rather than transcribed verbatim.

---

### Prompt 1 — Initial spec (project kickoff)

> An internal team manages a growing body of knowledge — policy documents,
> process guides, and FAQs — alongside a structured employee and project
> database. Today, finding answers requires switching between document
> search and database queries manually.
>
> Your task is to build a conversational AI agent that unifies these two
> sources: it should accept a plain-language question, retrieve what is
> relevant from whichever source — or both — and respond with a
> synthesized answer. The agent is for internal use and runs entirely on a
> local machine.
>
> [Full functional requirements, hard constraints (Python only, fully
> local, LangGraph + ChromaDB + sqlite3 + sentence-transformers required,
> NVIDIA NIM `nvidia/nemotron-3.5-lightning-30b-a3b` as the LLM, no
> LlamaIndex/LangChain pre-built RAG chains), and deliverables (repo,
> prompt log, demo) as given in the assignment.]

This was the driving prompt for the entire build. From it, the agent
planned out: a hand-rolled chunking + embedding + Chroma ingestion
pipeline, a SQLite schema + NL-to-SQL layer with safety validation, an
explicit/traceable router, a LangGraph state machine with a grade→retry
loop, and a CLI with session memory.

---

### Prompt 2 — "Continue"

> Continue

Follow-up prompt to resume after the agent reported partial progress
(core modules built and unit-tested, README/prompt log/demo transcript
still outstanding). Directed the agent to finish packaging the remaining
deliverables.

---

## Key internal design prompts the agent used against itself

These weren't sent by the human operator but are the prompts embedded in
the code that drive the LLM at runtime — included here since they're the
actual "prompts" doing the intelligent work described in the requirements
(routing, NL-to-SQL, grading, synthesis):

**Router system prompt** (`src/router.py`) — asks the model to output
exactly `ROUTE: <docs|database|both>` / `REASON: ...` given a description
of both sources, so the routing decision is a discrete, parseable, logged
value rather than an implicit side effect.

**NL-to-SQL system prompt** (`src/db_tools.py`) — constrains the model to
emit a single read-only `SELECT` against a fixed schema description, or
`NO_QUERY` if the schema can't answer the question, so it can be validated
before execution.

**Grader system prompt** (`src/grader.py`) — asks for a single-word
`SUFFICIENT`/`INSUFFICIENT` verdict on whether retrieved context actually
answers the question, used to trigger the reformulate-and-retry loop.

**Reformulation prompt** (`src/graph.py::node_reformulate`) — asks the
model to rewrite the original question to be more retrievable, given the
failed first attempt.

**Synthesis system prompt** (`src/graph.py::node_synthesize`) — instructs
the model to answer *only* from the provided context, cite which source(s)
it used, and explicitly say when it doesn't have enough information rather
than fabricating — this is what satisfies the "uncertainty acknowledgement"
requirement at the answer-generation layer.

---

## Testing prompts (sandbox constraints)

During development the agent discovered it could not install full
`torch`/`sentence-transformers` in the sandbox (disk quota) and could not
reach `integrate.api.nvidia.com` from the sandbox network (network egress
blocks that host). The agent's own internal reasoning/self-directed
prompts at that point were, in effect:

> "I can't install torch or reach the NIM endpoint from here. Build a
> lightweight stub embedder and a mocked `llm_client.chat()` so the actual
> shipped code (routing, retrieval, SQL safety, grading, retry logic, CLI
> memory) can still be exercised end-to-end and verified for correctness,
> while being transparent that the *wording* of final answers requires a
> real API key and a real embedding model on the user's machine."

This produced `scripts/mock_llm_test.py`, used only for local verification
— it is not part of the runtime agent and is not required to use the
project.
