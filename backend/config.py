import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Settings(BaseModel):
    PROJECT_NAME: str = "GovContractFinder"
    DATA_DIR: Path = BASE_DIR / "data"
    DB_PATH: Path = BASE_DIR / "data" / "contracts.db"
    SKILLS_FILE_PATH: Path = BASE_DIR / "data" / "skills.json"
    
    # SAM.gov API configuration
    SAM_API_KEY: str = os.getenv("SAM_API_KEY", "")
    SAM_API_BASE_URL: str = os.getenv("SAM_API_BASE_URL", "https://api.sam.gov/opportunities/v2/search")
    
    # Schedule configuration (Default: 5:00 PM EST daily)
    SCHEDULE_HOUR: int = int(os.getenv("SCHEDULE_HOUR", "17"))
    SCHEDULE_MINUTE: int = int(os.getenv("SCHEDULE_MINUTE", "0"))
    SCHEDULE_TIMEZONE: str = os.getenv("SCHEDULE_TIMEZONE", "America/New_York")
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
