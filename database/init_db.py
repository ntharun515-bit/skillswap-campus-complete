"""One-command database setup: creates tables + seeds demo data."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use SQLite by default for easy local setup (set USE_SQLITE=false + DATABASE_URL for MySQL)
os.environ.setdefault("USE_SQLITE", "true")

from database.seed import seed  # noqa: E402

if __name__ == "__main__":
    print("Initializing SkillSwap database...")
    seed()
    print("Done. Run: python run.py")
