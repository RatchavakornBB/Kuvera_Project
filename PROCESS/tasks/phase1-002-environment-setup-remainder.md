Scope: backend/, agents/, supabase/, .env.example (root)
Depends on: none
Files allowed to touch: backend/, agents/, supabase/, .env.example, root README if needed
DoD:
  - [x] /backend FastAPI scaffold: app starts with `uvicorn app.main:app`, responds on a health-check route
  - [x] config.py validates required keys at startup and fails fast, naming the missing key (ANTHROPIC_API_KEY required; OPENAI_API_KEY/GOOGLE_API_KEY/DEEPGRAM_API_KEY optional; SUPABASE_URL/SUPABASE_KEY required)
  - [x] requirements.txt: fastapi, uvicorn, langgraph, langchain-anthropic, supabase-py, python-dotenv
  - [x] /agents folder structure created (nodes/, adapters/) — actual model_adapter + node implementation is Phase 2 scope, not this task; graph.py deferred to Phase 2 too (no placeholder file written, to avoid a fake-looking stub)
  - [x] supabase init && supabase start — `supabase status` / `docker ps` shows Postgres/Auth/Storage/Realtime healthy locally, on shifted ports (55321-55329) due to a port conflict with an unrelated already-running project
  - [x] .env.example documents every key from config.py
  - [x] .env is gitignored (already covered by root .gitignore), never committed
