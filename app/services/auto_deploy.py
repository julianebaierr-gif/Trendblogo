import os
import shutil
import subprocess
import threading
import logging
from pathlib import Path

logger = logging.getLogger("trendblogo.auto_deploy")

def run_auto_deploy() -> dict:
    """
    Syncs the active SQLite database to app/trendblogo_seed.db,
    commits changes, and pushes to vercel-repo (which triggers automatic live Vercel build).
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_file = base_dir / "trendblogo.db"
    seed_file = base_dir / "app" / "trendblogo_seed.db"
    
    # 1. Sync live DB to seed DB
    if db_file.exists():
        try:
            shutil.copy2(db_file, seed_file)
            logger.info("Successfully copied trendblogo.db to app/trendblogo_seed.db")
        except Exception as e:
            logger.error(f"Error copying DB to seed: {e}")
            return {"status": "error", "message": f"DB sync failed: {e}"}

    # 2. Commit and push to git
    try:
        subprocess.run(["git", "add", "app/trendblogo_seed.db"], cwd=base_dir, check=False)
        commit_res = subprocess.run(
            ["git", "commit", "-m", "Auto-deploy: sync database and published articles to live site"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        push_vercel = subprocess.run(
            ["git", "push", "vercel-repo", "main"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        subprocess.run(
            ["git", "push", "origin", "main"],
            cwd=base_dir,
            capture_output=True,
            text=True
        )
        return {
            "status": "success",
            "message": "Auto-deploy triggered successfully. Vercel build is live.",
            "output": push_vercel.stdout or commit_res.stdout
        }
    except Exception as e:
        logger.error(f"Git auto-deploy failed: {e}")
        return {"status": "error", "message": str(e)}

def trigger_auto_deploy_background():
    """Runs auto-deployment in a separate background daemon thread."""
    t = threading.Thread(target=run_auto_deploy, daemon=True)
    t.start()
