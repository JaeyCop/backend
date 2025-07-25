import uvicorn
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from app.main import app

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )