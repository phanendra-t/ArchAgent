from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.api.review import router as review_router
from app.api.feedback import router as feedback_router
from app.api.validate import router as validate_router
from app.api.reviews import router as reviews_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database connection pool
    try:
        from app.db.client import get_pool, close_pool
        pool = await get_pool()
        print("Database connection pool initialized")

        # Auto-create tables if they don't exist
        await pool.execute("""
            CREATE EXTENSION IF NOT EXISTS vector;

            CREATE TABLE IF NOT EXISTS reviews (
                id SERIAL PRIMARY KEY,
                review_id VARCHAR(64) UNIQUE NOT NULL,
                system_name VARCHAR(128) NOT NULL DEFAULT 'unknown',
                diff_hash VARCHAR(64) NOT NULL,
                diff_preview TEXT,
                spec_file VARCHAR(256),
                health_score INT NOT NULL DEFAULT 100,
                summary TEXT,
                findings JSONB NOT NULL DEFAULT '[]'::jsonb,
                suppressed_findings JSONB NOT NULL DEFAULT '[]'::jsonb,
                stats JSONB NOT NULL DEFAULT '{}'::jsonb,
                reward_model_active BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS annotations (
                id SERIAL PRIMARY KEY,
                finding_id VARCHAR(64) NOT NULL,
                review_id VARCHAR(64),
                finding_text TEXT NOT NULL DEFAULT '',
                finding_category VARCHAR(32) NOT NULL DEFAULT '',
                finding_severity VARCHAR(16) NOT NULL DEFAULT '',
                rule_violated VARCHAR(128),
                context_violated VARCHAR(64),
                label VARCHAR(16) NOT NULL CHECK (label IN ('valid', 'false_positive', 'partial')),
                severity_accuracy INT CHECK (severity_accuracy BETWEEN 1 AND 5),
                explanation_quality INT CHECK (explanation_quality BETWEEN 1 AND 5),
                actionability INT CHECK (actionability BETWEEN 1 AND 5),
                embedding vector(384),
                created_at TIMESTAMP DEFAULT NOW()
            );

            CREATE TABLE IF NOT EXISTS model_metrics (
                id SERIAL PRIMARY KEY,
                annotation_count INT,
                accuracy FLOAT,
                precision_score FLOAT,
                recall_score FLOAT,
                f1_score FLOAT,
                threshold FLOAT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        print("Database schema verified")
    except Exception as e:
        print(f"Warning: database pool not initialized: {e}")

    # Warm up embedding model on startup
    try:
        from app.reward.embeddings import _get_embedding_model
        _get_embedding_model()
        print("Embedding model loaded")
    except Exception as e:
        print(f"Warning: embedding model not loaded at startup: {e}")

    # Try to load reward model
    try:
        from app.reward.model import get_reward_model
        rm = get_reward_model()
        if rm.is_available():
            print("Reward model loaded")
    except Exception:
        pass

    yield

    # Cleanup
    try:
        from app.db.client import close_pool
        await close_pool()
        print("Database connection pool closed")
    except Exception:
        pass


app = FastAPI(
    title="ArchAgent",
    description="Agentic Code Review with Architectural Intent Understanding",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(review_router, prefix="/api", tags=["review"])
app.include_router(reviews_router, prefix="/api", tags=["reviews"])
app.include_router(feedback_router, prefix="/api", tags=["feedback"])
app.include_router(validate_router, prefix="/api", tags=["validate"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "archagent"}