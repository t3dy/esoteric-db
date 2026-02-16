# Esoteric Studies Database (Seed)

This is the "Seed" implementation of your Esoteric Studies Database.

## Features
*   **Scanner:** `scan.py` indexes your PDFs, creates a robust SQLite database, and exports JSON.
*   **Database:** A SQLite DB (`esoteric.db`) with a core schema for documents plus empty tables ("Nubs") for future features like Full Text Search, Knowledge Graph, and Chat Logs.
*   **Dashboard:** A generic `index.html` viewer that loads the exported JSON.

## Quick Start

### 1. Requirements
*   Python 3.x
*   No external pip packages needed for the basic text-only scan! (Uses standard lib `sqlite3`, `json`, `hashlib`, `os`).

### 2. Run the Scan
1.  Place your PDFs in a folder (or use the current folder).
2.  Run the scanner:
    ```bash
    python scan.py --dir "C:/path/to/your/pdf/library"
    ```
    *(If you run it without arguments, it scans the current directory)*.

3.  This will create:
    *   `esoteric.db` (The SQLite Source of Truth)
    *   `docs/` folder containing:
        *   `docs.json`
        *   `stats.json`
        *   `config.json`

### 3. View the Dashboard Locally
1.  Go to the `docs/` folder.
2.  You likely need a lightweight server because modern browsers block `fetch` from `file://` URLs.
    ```bash
    cd docs
    python -m http.server
    ```
3.  Open `http://localhost:8000` in your browser.

## Deploying to GitHub Pages

1.  **Initialize Git:**
    ```bash
    git init
    git add .
    git commit -m "Initial commit of Esoteric Seed"
    ```

2.  **Create a Repo on GitHub:**
    *   Go to GitHub.com -> New Repository.
    *   Name it (e.g., `esoteric-db`).

3.  **Push:**
    ```bash
    git remote add origin https://github.com/YOUR_USERNAME/esoteric-db.git
    git branch -M main
    git push -u origin main
    ```

4.  **Enable Pages:**
    *   Go to Repository Settings -> **Pages**.
    *   Under "Build and deployment", select **Source** -> `Deploy from a branch`.
    *   Select Branch: `main`, Folder: `/docs` (Important! Select the docs folder, not root).
    *   Click Save.

5.  **Done!**
    Your dashboard will be live at `https://YOUR_USERNAME.github.io/esoteric-db/`.
