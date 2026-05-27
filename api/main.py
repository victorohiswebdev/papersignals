"""PaperSignals API — FastAPI backend for the Phase 3 dashboard.

Provides REST endpoints for document analysis, history, and corpus stats.
Wraps the existing papersignals analysis pipeline.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import tempfile
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from papersignals.cli import run_analysis
from papersignals.corpus.corpus_db import CorpusDB
from papersignals.core.scoring import compute_rf_score

logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────
DATA_DIR = Path.home() / ".papersignals" / "api"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "history.db"
UPLOAD_DIR = DATA_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


# ── Database ────────────────────────────────────────────────────────

def init_db():
    """Initialize the SQLite database for analysis history."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            word_count INTEGER,
            composite_score REAL,
            rf_score REAL,
            rf_class INTEGER,
            risk TEXT,
            created_at TEXT NOT NULL,
            result_json TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_analyses_created
        ON analyses(created_at DESC)
    """)
    conn.commit()
    conn.close()


def save_analysis(analysis_id: str, filename: str, result: Dict) -> None:
    """Save an analysis result to the database."""
    comp = result.get("composite", {})
    rf = result.get("rf_classifier", {})

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute(
        """INSERT OR REPLACE INTO analyses
           (id, filename, word_count, composite_score, rf_score, rf_class, risk, created_at, result_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            analysis_id,
            filename,
            result.get("segments", {}).get("word_count", 0),
            comp.get("composite_score"),
            rf.get("rf_score"),
            rf.get("rf_class"),
            rf.get("risk", comp.get("risk")),
            datetime.now().isoformat(),
            json.dumps(result, default=str),
        ),
    )
    conn.commit()
    conn.close()


def get_analysis(analysis_id: str) -> Optional[Dict]:
    """Retrieve a single analysis by ID."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return dict(row)


def list_analyses(limit: int = 50, offset: int = 0) -> List[Dict]:
    """List recent analyses with summary info."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT id, filename, word_count, composite_score,
                  rf_score, rf_class, risk, created_at
           FROM analyses
           ORDER BY created_at DESC
           LIMIT ? OFFSET ?""",
        (limit, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── Models ──────────────────────────────────────────────────────────

class AnalysisResponse(BaseModel):
    id: str
    filename: str
    word_count: int
    composite_score: Optional[float] = None
    rf_score: Optional[float] = None
    rf_class: Optional[int] = None
    risk: str
    created_at: str
    signals: Optional[Dict[str, Any]] = None
    recommendations: Optional[List[str]] = None


class SignalInfo(BaseModel):
    id: str
    name: str
    description: str
    weight: float
    icon: str


class StatusResponse(BaseModel):
    version: str
    corpus_papers: int
    corpus_analyzed: int
    classifier_available: bool
    api_uptime: float


# ── FastAPI App ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    init_db()
    yield


app = FastAPI(
    title="PaperSignals API",
    description="Analyze academic writing for AI detection signals",
    version="0.3.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Track uptime
_start_time = time.time()


# ── Routes ──────────────────────────────────────────────────────────

@app.get("/api/status", response_model=StatusResponse)
async def get_status():
    """API health check with corpus and classifier status."""
    db = CorpusDB()
    rf_path = Path.home() / ".papersignals" / "models" / "rf_classifier.joblib"

    return StatusResponse(
        version="0.3.0",
        corpus_papers=db.total_papers(),
        corpus_analyzed=db.total_analyzed(),
        classifier_available=rf_path.exists(),
        api_uptime=time.time() - _start_time,
    )


@app.get("/api/signals")
async def get_signals():
    """List available analysis signals with descriptions."""
    signals = [
        {
            "id": "burstiness",
            "name": "Burstiness",
            "description": "Measures sentence length variance. Human writing naturally mixes short and long sentences; AI text tends toward uniform lengths.",
            "weight": 0.25,
            "icon": "📏",
        },
        {
            "id": "transition_density",
            "name": "Transition Density",
            "description": "Frequency and variety of transitional phrases. AI relies heavily on a narrow set of signposting words.",
            "weight": 0.15,
            "icon": "🔗",
        },
        {
            "id": "lexical_diversity",
            "name": "Lexical Diversity",
            "description": "Range of vocabulary used. AI text reuses a narrower vocabulary than human writing.",
            "weight": 0.20,
            "icon": "📖",
        },
        {
            "id": "vocabulary_fingerprint",
            "name": "Vocabulary Fingerprint",
            "description": "Detects words statistically over-represented in AI academic text (e.g., 'delve', 'leverage', 'robust').",
            "weight": 0.15,
            "icon": "🔤",
        },
        {
            "id": "paragraph_uniformity",
            "name": "Paragraph Uniformity",
            "description": "Consistency of paragraph lengths. AI produces paragraphs of very similar length.",
            "weight": 0.10,
            "icon": "📐",
        },
        {
            "id": "readability",
            "name": "Readability",
            "description": "Flesch-Kincaid and Gunning Fog scores. Academic human writing typically falls in specific readability ranges.",
            "weight": 0.10,
            "icon": "📊",
        },
        {
            "id": "perplexity",
            "name": "Perplexity (approx.)",
            "description": "A rough estimate of how predictable your word choices are. Lower perplexity can indicate AI generation.",
            "weight": 0.05,
            "icon": "🎲",
        },
    ]
    return {"signals": signals}


@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_document(file: UploadFile = File(...)):
    """Upload and analyze a document.

    Accepts .txt, .md, and .docx files. Returns a full score report
    with per-signal breakdown and RF classifier probability.
    """
    # Validate file type
    ext = Path(file.filename or "upload.txt").suffix.lower()
    if ext not in (".txt", ".md", ".docx"):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Supported: .txt, .md, .docx",
        )

    # Save uploaded file
    analysis_id = str(uuid.uuid4())[:8]
    upload_path = UPLOAD_DIR / f"{analysis_id}{ext}"
    content = await file.read()

    # Check file size (max 10MB)
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Max 10MB.")

    upload_path.write_bytes(content)

    try:
        # Run analysis
        result = run_analysis(str(upload_path))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Analysis failed: {str(e)}",
        )
    finally:
        # Clean up uploaded file
        if upload_path.exists():
            upload_path.unlink()

    # Save to history
    save_analysis(analysis_id, file.filename or "unnamed", result)

    # Build response
    comp = result.get("composite", {})
    rf = result.get("rf_classifier", {})
    segments = result.get("segments", {})

    return AnalysisResponse(
        id=analysis_id,
        filename=file.filename or "unnamed",
        word_count=segments.get("word_count", 0),
        composite_score=comp.get("composite_score"),
        rf_score=rf.get("rf_score"),
        rf_class=rf.get("rf_class"),
        risk=rf.get("risk", comp.get("risk", "medium")),
        created_at=datetime.now().isoformat(),
        signals=result.get("signals"),
        recommendations=_generate_recommendations(result),
    )


@app.get("/api/analyze/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Retrieve a previously completed analysis by ID."""
    row = get_analysis(analysis_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Analysis not found")

    result = json.loads(row["result_json"])
    comp = result.get("composite", {})

    return {
        "id": row["id"],
        "filename": row["filename"],
        "word_count": row["word_count"],
        "composite_score": row["composite_score"],
        "rf_score": row["rf_score"],
        "rf_class": row["rf_class"],
        "risk": row["risk"],
        "created_at": row["created_at"],
        "signals": result.get("signals"),
        "recommendations": _generate_recommendations(result),
    }


@app.get("/api/analyses")
async def list_recent_analyses(limit: int = 20, offset: int = 0):
    """List recent analyses (summary only)."""
    analyses = list_analyses(limit=min(limit, 100), offset=offset)
    return {"analyses": analyses, "total": len(analyses)}


@app.delete("/api/analyze/{analysis_id}")
async def delete_analysis(analysis_id: str):
    """Delete an analysis record."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    if deleted == 0:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"deleted": analysis_id}


# ── Helpers ─────────────────────────────────────────────────────────

def _generate_recommendations(result: Dict) -> List[str]:
    """Generate actionable recommendations from analysis results."""
    signals = result.get("signals", {})
    recs: List[str] = []

    # Burstiness
    burst = signals.get("burstiness", {})
    if burst.get("risk") == "high":
        recs.append("📏 Vary sentence lengths — mix short and long sentences for a more natural rhythm.")
    elif burst.get("risk") == "medium":
        recs.append("📏 Improve sentence length variation to reduce repetitive patterns.")

    # Transitions
    trans = signals.get("transition_density", {})
    if trans.get("risk") == "high":
        recs.append("🔗 Reduce overt transition words — let logic connect ideas naturally.")

    # Lexical diversity
    lex = signals.get("lexical_diversity", {})
    if lex.get("risk") in ("high", "medium"):
        recs.append("📖 Broaden vocabulary — use synonyms and more varied word choices.")

    # Vocabulary fingerprint
    vocab = signals.get("vocabulary_fingerprint", {})
    if vocab.get("risk") == "high":
        recs.append("🔤 Replace AI-signaling vocabulary with more natural alternatives.")

    # Paragraph uniformity
    para = signals.get("paragraph_uniformity", {})
    if para.get("risk") == "high":
        recs.append("📐 Vary paragraph lengths — some can be short, others extended.")

    if not recs:
        recs.append("✅ Text appears natural. No specific recommendations.")

    return recs


# ── Entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
