# Meridian Internal Knowledge Agent

A conversational agent that unifies a company document corpus (policies,
process guides, FAQs) and a structured SQLite database (employees,
departments, projects) behind a single natural-language CLI. It decides
which source(s) to query, retrieves locally, and synthesizes one answer —
saying so explicitly when it doesn't have enough information rather than
guessing.

Everything runs locally except a single call per turn to the NVIDIA NIM
API for the LLM (`nvidia/nemotron-3.5-lightning-30b-a3b`). Embeddings,
the vector store, and the database all run on your machine.

## Architecture at a glance

```
question --> [router]        explicit LLM classification + keyword fallback,
                              decision logged to stdout
                |
                v
          [retrieve]         docs -> ChromaDB (local, sentence-transformers
                              embeddings) and/or database -> NL-to-SQL ->
                              validated read-only SQLite query
                |
                v
           [grade]           is retrieved context sufficient?
                |
        insufficient -> [reformulate] -> back to [router]  (max 1 retry)
                |
           sufficient
                |
                v
          [synthesize]       final answer grounded only in retrieved
                              context; explicit "I don't have enough
                              information" when context falls short
```

Built with `langgraph` (the state machine above), `chromadb` +
`sentence-transformers` (local vector retrieval), and `sqlite3` (local
structured retrieval). No LlamaIndex or LangChain pre-built RAG chains —
chunking, embedding calls, vector queries, and SQL generation/execution are
all implemented directly in this repo (see `src/`).

## Setup

1. **Clone and install dependencies** (Python 3.10+ recommended):
   ```bash
   pip install -r requirements.txt
   ```

2. **Get a free NVIDIA NIM API key**: go to build.nvidia.com → Settings →
   API Keys → Generate Personal Key.

3. **Configure your key**:
   ```bash
   cp .env.example .env
   # edit .env and paste your key into NVIDIA_API_KEY=
   ```

4. **Create the local database** (run once):
   ```bash
   python setup_database.py
   ```
   This creates `meridian.db` with sample departments, employees, and
   projects.

5. **Build the local vector index** (run once, or again any time you
   change files in `docs/`):
   ```bash
   python ingest.py
   ```
   This downloads the `all-MiniLM-L6-v2` embedding model on first run
   (cached locally afterward) and populates `./chroma_db`.

6. **Run the agent**:
   ```bash
   python main.py
   ```
   Type questions at the `You:` prompt. Type `reset` to clear session
   memory, `exit` to quit.

## Project layout

```
setup_database.py      # creates + populates meridian.db (provided asset workflow)
ingest.py               # chunks docs/, embeds locally, builds the Chroma index
docs/                   # 15 policy/process source documents
main.py                 # entry point
src/
  config.py             # paths, model names, thresholds — single source of truth
  llm_client.py         # thin wrapper around the NVIDIA NIM chat endpoint
  doc_tools.py           # vector store retrieval (Chroma + sentence-transformers)
  db_tools.py             # NL-to-SQL generation + safety-checked read-only execution
  router.py               # explicit source routing (docs / database / both)
  grader.py                # judges retrieval sufficiency, drives the retry loop
  graph.py                  # LangGraph state machine wiring it all together
  cli.py                     # interactive loop + session memory
scripts/
  mock_llm_test.py           # local dev harness (mocks the LLM) used to sanity-check
                              # the graph wiring without hitting the network — not
                              # required to run the real agent
```

## Notes

- The SQL layer only ever executes single, validated `SELECT` statements
  (see `src/db_tools.py::is_safe_select`) — no writes, no stacked
  statements, no schema changes, regardless of what the LLM generates.
- Routing decisions and retrieval traces are printed to the console
  (`[router]` / `[trace]` lines) so the decision process is visible while
  you use the CLI.
- If retrieval is judged insufficient, the agent reformulates the query
  once and retries before answering; if it's still insufficient, it tells
  you plainly instead of fabricating an answer.
