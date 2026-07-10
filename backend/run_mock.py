"""Compatibility launcher.

This project now uses the database configured in backend/.env.
The old version of this script switched the backend to temp_db.sqlite3, which
made the UI show mock data instead of the remote MySQL data.
"""

import uvicorn


if __name__ == "__main__":
    print("[INFO] run_mock.py no longer starts SQLite mock data.")
    print("[INFO] Starting app.main:app with backend/.env database settings.")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")
