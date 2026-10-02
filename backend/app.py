import os
import json
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query, Body, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import settings, BASE_DIR
from backend.database import (
    init_db,
    query_opportunities,
    get_opportunity_by_id,
    update_user_interaction,
    get_stats,
    save_scorecard,
    get_connection
)
from backend.scoring_engine import scoring_engine
from backend.sam_client import sam_client
from backend.scheduler import sync_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB tables
    init_db()
    # Start background scheduler (5:00 PM EST daily)
    sync_scheduler.start()
    
    # Run initial sync if database is empty so user immediately sees data
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM solicitations")
    count = c.fetchone()[0]
    conn.close()
    if count == 0:
        # Seed initial data asynchronously
        await sync_scheduler.execute_sync(source="INITIAL_SEED")
        
    yield
    # Shutdown scheduler
    sync_scheduler.shutdown()

app = FastAPI(
    title="GovContractFinder",
    description="SAM.gov Government Contract Finder & Executable Work Scorecard Engine",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = BASE_DIR / "frontend"

# Serve Frontend static assets
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

@app.get("/")
async def read_index():
    index_file = FRONTEND_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend index.html not found")
    return FileResponse(index_file)

# --- API Endpoints ---

@app.get("/api/opportunities")
async def list_opportunities(
    query: Optional[str] = Query(None, description="Search keyword in title, agency, or description"),
    min_score: Optional[float] = Query(None, description="Minimum match score (0-100)"),
    tier: Optional[str] = Query("ALL", description="Filter by tier: ALL, HIGH, MODERATE, LOW"),
    only_favorites: bool = Query(False, description="Filter only favorited contracts"),
    set_aside: Optional[str] = Query(None, description="Filter by set-aside type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0)
):
    results = query_opportunities(
        query=query,
        min_score=min_score,
        tier=tier,
        only_favorites=only_favorites,
        set_aside=set_aside,
        limit=limit,
        offset=offset
    )
    return {"results": results, "count": len(results)}

@app.get("/api/opportunities/{notice_id}")
async def get_opportunity(notice_id: str):
    opp = get_opportunity_by_id(notice_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Solicitation not found")
    return opp

class InteractionPayload(BaseModel):
    is_favorite: Optional[bool] = None
    status: Optional[str] = None
    notes: Optional[str] = None

@app.post("/api/opportunities/{notice_id}/interaction")
async def update_interaction(notice_id: str, payload: InteractionPayload):
    opp = get_opportunity_by_id(notice_id)
    if not opp:
        raise HTTPException(status_code=404, detail="Solicitation not found")
    update_user_interaction(
        notice_id=notice_id,
        is_favorite=payload.is_favorite,
        status=payload.status,
        notes=payload.notes
    )
    return {"status": "success", "notice_id": notice_id}

@app.post("/api/sync")
async def trigger_sync(background_tasks: BackgroundTasks, days_back: int = 2):
    if sync_scheduler.is_running_sync:
        return {"status": "in_progress", "message": "A sync is already executing"}
    
    # Run sync
    result = await sync_scheduler.execute_sync(source="MANUAL_TRIGGER", days_back=days_back)
    return result

@app.get("/api/schedule")
async def get_schedule():
    return sync_scheduler.get_schedule_info()

@app.get("/api/stats")
async def get_dashboard_stats():
    return get_stats()

@app.get("/api/skills")
async def get_skills_config():
    try:
        config = scoring_engine.load_skills_config()
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read skills file: {str(e)}")

@app.post("/api/skills")
async def update_skills_config(new_config: Dict[str, Any] = Body(...), recalculate: bool = Query(True)):
    try:
        # Validate JSON structure
        if "categories" not in new_config:
            raise HTTPException(status_code=400, detail="Skills config must contain 'categories' array")
            
        with open(settings.SKILLS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(new_config, f, indent=2)
            
        scoring_engine.reload()
        
        recalc_count = 0
        if recalculate:
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM solicitations")
            rows = c.fetchall()
            for r in rows:
                sol_dict = dict(r)
                scorecard = scoring_engine.calculate_scorecard(sol_dict)
                save_scorecard(scorecard)
                recalc_count += 1
            conn.close()
            
        return {
            "status": "success",
            "message": f"Skill sets file updated successfully. Recalculated {recalc_count} scorecards.",
            "recalculated_count": recalc_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update skills config: {str(e)}")

@app.post("/api/recalculate")
async def recalculate_all_scorecards():
    """
    Recalculates all scorecards with the current skill sets parameters
    """
    scoring_engine.reload()
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM solicitations")
    rows = c.fetchall()
    recalc_count = 0
    for r in rows:
        sol_dict = dict(r)
        scorecard = scoring_engine.calculate_scorecard(sol_dict)
        save_scorecard(scorecard)
        recalc_count += 1
    conn.close()
    return {"status": "success", "recalculated_count": recalc_count}

class ApiKeyPayload(BaseModel):
    api_key: str

@app.post("/api/settings/apikey")
async def save_api_key(payload: ApiKeyPayload):
    key = payload.api_key.strip()
    settings.SAM_API_KEY = key
    sam_client.api_key = key
    
    # Persist to .env file
    env_path = BASE_DIR / ".env"
    lines = []
    found = False
    if env_path.exists():
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines):
            if line.startswith("SAM_API_KEY="):
                lines[idx] = f"SAM_API_KEY={key}\n"
                found = True
                break
    if not found:
        lines.append(f"SAM_API_KEY={key}\n")
        
    with open(env_path, "w", encoding="utf-8") as f:
        f.writelines(lines)
        
    return {
        "status": "success",
        "has_api_key": bool(key),
        "message": "SAM.gov API Key saved successfully"
    }

@app.get("/api/settings/status")
async def get_settings_status():
    return {
        "has_sam_api_key": bool(settings.SAM_API_KEY and settings.SAM_API_KEY.strip()),
        "schedule": f"{settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} {settings.SCHEDULE_TIMEZONE}",
        "skills_file": str(settings.SKILLS_FILE_PATH.name)
    }
