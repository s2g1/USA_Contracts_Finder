import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.config import settings

def get_connection():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS solicitations (
        notice_id TEXT PRIMARY KEY,
        sol_number TEXT,
        title TEXT NOT NULL,
        agency TEXT,
        office TEXT,
        posted_date TEXT,
        response_date TEXT,
        naics_code TEXT,
        psc_code TEXT,
        set_aside TEXT,
        type TEXT,
        description TEXT,
        ui_link TEXT,
        place_of_performance TEXT,
        raw_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scorecards (
        notice_id TEXT PRIMARY KEY,
        overall_score REAL NOT NULL,
        tier TEXT NOT NULL,
        category_scores TEXT NOT NULL,
        matched_keywords TEXT NOT NULL,
        matched_naics INTEGER DEFAULT 0,
        summary TEXT NOT NULL,
        deliverables TEXT,
        feasibility_analysis TEXT,
        calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (notice_id) REFERENCES solicitations(notice_id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_interactions (
        notice_id TEXT PRIMARY KEY,
        is_favorite INTEGER DEFAULT 0,
        status TEXT DEFAULT 'NEW',
        notes TEXT DEFAULT '',
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (notice_id) REFERENCES solicitations(notice_id) ON DELETE CASCADE
    );
    """)
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sync_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sync_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        source TEXT NOT NULL,
        found_count INTEGER DEFAULT 0,
        new_count INTEGER DEFAULT 0,
        updated_count INTEGER DEFAULT 0,
        status TEXT NOT NULL,
        message TEXT
    );
    """)
    
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_scorecards_score ON scorecards(overall_score DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitations_posted ON solicitations(posted_date DESC);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_solicitations_naics ON solicitations(naics_code);")
    
    conn.commit()
    conn.close()

def upsert_solicitation(sol_data: Dict[str, Any]) -> tuple[bool, bool]:
    """
    Returns (is_new, is_updated)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    notice_id = sol_data["notice_id"]
    cursor.execute("SELECT notice_id, updated_at FROM solicitations WHERE notice_id = ?", (notice_id,))
    row = cursor.fetchone()
    
    now = datetime.utcnow().isoformat()
    raw_str = json.dumps(sol_data.get("raw_data", {}))
    
    if row:
        cursor.execute("""
        UPDATE solicitations SET
            sol_number = ?,
            title = ?,
            agency = ?,
            office = ?,
            posted_date = ?,
            response_date = ?,
            naics_code = ?,
            psc_code = ?,
            set_aside = ?,
            type = ?,
            description = ?,
            ui_link = ?,
            place_of_performance = ?,
            raw_data = ?,
            updated_at = ?
        WHERE notice_id = ?
        """, (
            sol_data.get("sol_number", ""),
            sol_data.get("title", ""),
            sol_data.get("agency", ""),
            sol_data.get("office", ""),
            sol_data.get("posted_date", ""),
            sol_data.get("response_date", ""),
            sol_data.get("naics_code", ""),
            sol_data.get("psc_code", ""),
            sol_data.get("set_aside", ""),
            sol_data.get("type", ""),
            sol_data.get("description", ""),
            sol_data.get("ui_link", f"https://sam.gov/opp/{notice_id}/view"),
            sol_data.get("place_of_performance", ""),
            raw_str,
            now,
            notice_id
        ))
        conn.commit()
        conn.close()
        return False, True
    else:
        cursor.execute("""
        INSERT INTO solicitations (
            notice_id, sol_number, title, agency, office, posted_date,
            response_date, naics_code, psc_code, set_aside, type,
            description, ui_link, place_of_performance, raw_data,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            notice_id,
            sol_data.get("sol_number", ""),
            sol_data.get("title", ""),
            sol_data.get("agency", ""),
            sol_data.get("office", ""),
            sol_data.get("posted_date", ""),
            sol_data.get("response_date", ""),
            sol_data.get("naics_code", ""),
            sol_data.get("psc_code", ""),
            sol_data.get("set_aside", ""),
            sol_data.get("type", ""),
            sol_data.get("description", ""),
            sol_data.get("ui_link", f"https://sam.gov/opp/{notice_id}/view"),
            sol_data.get("place_of_performance", ""),
            raw_str,
            now,
            now
        ))
        # Initialize default interaction record
        cursor.execute("""
        INSERT OR IGNORE INTO user_interactions (notice_id, is_favorite, status, notes)
        VALUES (?, 0, 'NEW', '')
        """, (notice_id,))
        conn.commit()
        conn.close()
        return True, False

def save_scorecard(scorecard_data: Dict[str, Any]):
    conn = get_connection()
    cursor = conn.cursor()
    
    category_scores_str = json.dumps(scorecard_data.get("category_scores", {}))
    matched_keywords_str = json.dumps(scorecard_data.get("matched_keywords", []))
    deliverables_str = json.dumps(scorecard_data.get("deliverables", []))
    feasibility_str = json.dumps(scorecard_data.get("feasibility_analysis", {}))
    
    cursor.execute("""
    INSERT INTO scorecards (
        notice_id, overall_score, tier, category_scores, matched_keywords,
        matched_naics, summary, deliverables, feasibility_analysis, calculated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    ON CONFLICT(notice_id) DO UPDATE SET
        overall_score = excluded.overall_score,
        tier = excluded.tier,
        category_scores = excluded.category_scores,
        matched_keywords = excluded.matched_keywords,
        matched_naics = excluded.matched_naics,
        summary = excluded.summary,
        deliverables = excluded.deliverables,
        feasibility_analysis = excluded.feasibility_analysis,
        calculated_at = CURRENT_TIMESTAMP
    """, (
        scorecard_data["notice_id"],
        scorecard_data["overall_score"],
        scorecard_data["tier"],
        category_scores_str,
        matched_keywords_str,
        1 if scorecard_data.get("matched_naics") else 0,
        scorecard_data.get("summary", ""),
        deliverables_str,
        feasibility_str
    ))
    conn.commit()
    conn.close()

def log_sync(source: str, found_count: int, new_count: int, updated_count: int, status: str, message: str = ""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO sync_logs (source, found_count, new_count, updated_count, status, message)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (source, found_count, new_count, updated_count, status, message))
    conn.commit()
    conn.close()

def get_latest_sync_log() -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sync_logs ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def query_opportunities(
    query: Optional[str] = None,
    min_score: Optional[float] = None,
    tier: Optional[str] = None,
    only_favorites: bool = False,
    set_aside: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    
    sql = """
    SELECT 
        s.notice_id,
        s.sol_number,
        s.title,
        s.agency,
        s.office,
        s.posted_date,
        s.response_date,
        s.naics_code,
        s.psc_code,
        s.set_aside,
        s.type,
        s.description,
        s.ui_link,
        s.place_of_performance,
        s.updated_at,
        sc.overall_score,
        sc.tier,
        sc.category_scores,
        sc.matched_keywords,
        sc.matched_naics,
        sc.summary,
        sc.deliverables,
        sc.feasibility_analysis,
        ui.is_favorite,
        ui.status as user_status,
        ui.notes
    FROM solicitations s
    LEFT JOIN scorecards sc ON s.notice_id = sc.notice_id
    LEFT JOIN user_interactions ui ON s.notice_id = ui.notice_id
    WHERE 1=1
    """
    params: List[Any] = []
    
    if query:
        q_wildcard = f"%{query}%"
        sql += " AND (s.title LIKE ? OR s.description LIKE ? OR s.agency LIKE ? OR s.sol_number LIKE ?)"
        params.extend([q_wildcard, q_wildcard, q_wildcard, q_wildcard])
        
    if min_score is not None:
        sql += " AND sc.overall_score >= ?"
        params.append(min_score)
        
    if tier and tier.upper() != "ALL":
        sql += " AND sc.tier = ?"
        params.append(tier.upper())
        
    if only_favorites:
        sql += " AND ui.is_favorite = 1"
        
    if set_aside and set_aside.upper() != "ALL":
        sql += " AND s.set_aside LIKE ?"
        params.append(f"%{set_aside}%")
        
    sql += " ORDER BY sc.overall_score DESC, s.posted_date DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    
    results = []
    for r in rows:
        item = dict(r)
        # Parse JSON fields
        for json_col in ["category_scores", "matched_keywords", "deliverables", "feasibility_analysis"]:
            if item.get(json_col):
                try:
                    item[json_col] = json.loads(item[json_col])
                except Exception:
                    pass
        results.append(item)
        
    conn.close()
    return results

def get_opportunity_by_id(notice_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT 
        s.*,
        sc.overall_score,
        sc.tier,
        sc.category_scores,
        sc.matched_keywords,
        sc.matched_naics,
        sc.summary,
        sc.deliverables,
        sc.feasibility_analysis,
        ui.is_favorite,
        ui.status as user_status,
        ui.notes
    FROM solicitations s
    LEFT JOIN scorecards sc ON s.notice_id = sc.notice_id
    LEFT JOIN user_interactions ui ON s.notice_id = ui.notice_id
    WHERE s.notice_id = ?
    """, (notice_id,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return None
        
    item = dict(row)
    for json_col in ["category_scores", "matched_keywords", "deliverables", "feasibility_analysis", "raw_data"]:
        if item.get(json_col):
            try:
                item[json_col] = json.loads(item[json_col])
            except Exception:
                pass
    return item

def update_user_interaction(notice_id: str, is_favorite: Optional[bool] = None, status: Optional[str] = None, notes: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT notice_id FROM user_interactions WHERE notice_id = ?", (notice_id,))
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute("INSERT INTO user_interactions (notice_id) VALUES (?)", (notice_id,))
        
    updates = []
    params = []
    if is_favorite is not None:
        updates.append("is_favorite = ?")
        params.append(1 if is_favorite else 0)
    if status is not None:
        updates.append("status = ?")
        params.append(status)
    if notes is not None:
        updates.append("notes = ?")
        params.append(notes)
        
    if updates:
        updates.append("updated_at = CURRENT_TIMESTAMP")
        sql = f"UPDATE user_interactions SET {', '.join(updates)} WHERE notice_id = ?"
        params.append(notice_id)
        cursor.execute(sql, params)
        conn.commit()
    conn.close()

def get_stats() -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM solicitations")
    total_solicitations = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scorecards WHERE tier = 'HIGH'")
    high_match_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM scorecards WHERE tier = 'MODERATE'")
    mod_match_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM user_interactions WHERE is_favorite = 1")
    favorites_count = cursor.fetchone()[0]
    
    conn.close()
    return {
        "total_solicitations": total_solicitations,
        "high_match_count": high_match_count,
        "moderate_match_count": mod_match_count,
        "favorites_count": favorites_count
    }
