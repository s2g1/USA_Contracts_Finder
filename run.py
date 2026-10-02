import socket
import uvicorn
import logging
from backend.config import settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("GovContractFinder")

def get_local_ip() -> str:
    """Finds the local network IP for mobile device access over Wi-Fi"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    local_ip = get_local_ip()
    port = settings.PORT

    print("\n" + "=" * 65)
    print(" 🚀 GovContractFinder - SAM.gov Solicitations & Scorecard Engine")
    print("=" * 65)
    print(f" [•] Web App URL:      http://localhost:{port}")
    print(f" [•] Mobile Access:    http://{local_ip}:{port}")
    print(f" [•] Daily Query Time: {settings.SCHEDULE_HOUR:02d}:{settings.SCHEDULE_MINUTE:02d} {settings.SCHEDULE_TIMEZONE}")
    print(f" [•] Skills File:      {settings.SKILLS_FILE_PATH}")
    print("=" * 65 + "\n")

    uvicorn.run(
        "backend.app:app",
        host=settings.HOST,
        port=settings.PORT,
        log_level="info",
        reload=False
    )
