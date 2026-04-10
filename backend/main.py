"""PM Productivity Agent — FastAPI entry point + CLI."""

import argparse
import logging
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.storage import db
from backend import config

# Configure logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)
logging.basicConfig(level=logging.INFO)

# ── FastAPI app ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="PM Productivity Agent",
    description="Evidence-backed weekly coaching for PM teams",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[config.FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
from backend.api.dashboard import router as dashboard_router
from backend.api.activities import router as activities_router
from backend.api.priorities import router as priorities_router
from backend.api.recommendations import router as recommendations_router
from backend.api.pm_views import router as pm_router
from backend.api.chat import router as chat_router

app.include_router(dashboard_router)
app.include_router(activities_router)
app.include_router(priorities_router)
app.include_router(recommendations_router)
app.include_router(pm_router)
app.include_router(chat_router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


@app.on_event("startup")
def startup():
    db.init_db()


# ── Pipeline trigger endpoint ──────────────────────────────────────────────────

@app.post("/api/pipeline/run")
def trigger_pipeline(use_llm: bool = True):
    from backend.agents.orchestrator import run_pipeline
    return run_pipeline(triggered_by="api", use_llm=use_llm)


@app.get("/api/pipeline/status")
def pipeline_status():
    run = db.get_last_pipeline_run()
    return run or {"status": "no runs yet"}


# ── CLI ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="PM Productivity Agent")
    parser.add_argument("--seed", action="store_true", help="Seed database with mock data")
    parser.add_argument("--run-pipeline", action="store_true", help="Run the analysis pipeline")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM for classification/recs (requires ANTHROPIC_API_KEY)")
    parser.add_argument("--serve", action="store_true", help="Start the API server")
    parser.add_argument("--port", type=int, default=config.API_PORT, help="API server port")
    args = parser.parse_args()

    if args.seed:
        from backend.seed.seed_data import seed_all
        print("Seeding database...")
        result = seed_all()
        print(f"Done! {result}")

    if args.run_pipeline:
        from backend.agents.orchestrator import run_pipeline
        print("Running pipeline...")
        result = run_pipeline(use_llm=args.use_llm)
        print(f"Pipeline result: {result}")

    if args.serve or (not args.seed and not args.run_pipeline):
        import uvicorn
        db.init_db()
        print(f"Starting PM Agent API on http://0.0.0.0:{args.port}")
        uvicorn.run(app, host="0.0.0.0", port=args.port)


if __name__ == "__main__":
    main()
