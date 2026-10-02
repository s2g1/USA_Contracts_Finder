import asyncio
from fastapi.testclient import TestClient
from backend.app import app

def test_endpoints():
    with TestClient(app) as client:
        # Test index page
        resp_index = client.get("/")
        print("GET / -> Status:", resp_index.status_code, "Length:", len(resp_index.text))
        assert resp_index.status_code == 200
        assert "GovContractFinder" in resp_index.text

        # Test opportunities
        resp_opps = client.get("/api/opportunities")
        print("GET /api/opportunities -> Status:", resp_opps.status_code, "Count:", resp_opps.json()["count"])
        assert resp_opps.status_code == 200
        assert resp_opps.json()["count"] > 0

        # Test single opportunity detail
        first_id = resp_opps.json()["results"][0]["notice_id"]
        resp_single = client.get(f"/api/opportunities/{first_id}")
        print(f"GET /api/opportunities/{first_id} -> Status:", resp_single.status_code)
        assert resp_single.status_code == 200
        assert "scorecards" not in resp_single.text  # checking clean model
        assert "overall_score" in resp_single.json()

        # Test schedule info
        resp_sched = client.get("/api/schedule")
        print("GET /api/schedule -> Status:", resp_sched.status_code, "Schedule:", resp_sched.json()["schedule"])
        assert resp_sched.status_code == 200
        assert resp_sched.json()["schedule"] == "17:00 America/New_York"

        # Test stats
        resp_stats = client.get("/api/stats")
        print("GET /api/stats -> Status:", resp_stats.status_code, resp_stats.json())
        assert resp_stats.status_code == 200

        # Test skills configuration
        resp_skills = client.get("/api/skills")
        print("GET /api/skills -> Status:", resp_skills.status_code, "Categories:", len(resp_skills.json()["categories"]))
        assert resp_skills.status_code == 200

        # Test user bookmark interaction
        resp_int = client.post(f"/api/opportunities/{first_id}/interaction", json={"is_favorite": True})
        print(f"POST /api/opportunities/{first_id}/interaction -> Status:", resp_int.status_code)
        assert resp_int.status_code == 200

        print("\nAll API endpoints passed successfully!")

if __name__ == "__main__":
    test_endpoints()
