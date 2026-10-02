import asyncio
from backend.config import settings
from backend.database import init_db, query_opportunities, get_stats
from backend.scoring_engine import scoring_engine
from backend.scheduler import sync_scheduler

def main():
    print("DB Path:", settings.DB_PATH)
    print("Skills File:", settings.SKILLS_FILE_PATH)
    init_db()
    print("DB initialized.")

    async def run_sync():
        res = await sync_scheduler.execute_sync(source="TEST_VERIFICATION")
        print("Sync execution status:", res["status"])
        print("Message:", res["message"])

    asyncio.run(run_sync())

    opps = query_opportunities()
    print(f"\nTotal opportunities in DB: {len(opps)}")
    print("-" * 60)
    for o in opps:
        print(f"[{o['tier']}] Score: {o['overall_score']}% | {o['title']}")
        print(f"  Agency: {o['agency']} | Set-Aside: {o['set_aside']}")
        print(f"  Summary: {o['summary'][:110]}...")
        print(f"  Keywords: {o['matched_keywords']}")
        print(f"  SAM Link: {o['ui_link']}")
        print("-" * 60)

    stats = get_stats()
    print("\nDashboard Stats:", stats)

if __name__ == "__main__":
    main()
