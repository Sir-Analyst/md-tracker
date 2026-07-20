# MD Tracker

Interactive markdown course and project progress tracker with a graphical dashboard.

![Dashboard](https://img.shields.io/badge/Dashboard-Chart.js-blue) ![Backend](https://img.shields.io/badge/Backend-FastAPI-green) ![DB](https://img.shields.io/badge/DB-SQLite-orange)

## Features

- **Track any markdown file** — add `.md` files by path to start tracking
- **Automatic step detection** — parses `##` / `###` headers and numbered lists as trackable steps
- **Interactive checkboxes** — tick/untick steps, progress saved to SQLite in real-time
- **Dashboard** — summary cards, doughnut chart (overall), bar chart (per-file comparison)
- **Viewer** — full markdown rendering with embedded checkboxes and progress bar
- **Rescan** — re-parse a file to pick up new steps without losing progress
- **Expand/Collapse** — collapse h3 sections in the viewer

## Quick Start

```powershell
# 1. Setup (creates venv + installs dependencies)
.\setup.ps1

# 2. Launch
.\launch.bat
```

Then open **http://127.0.0.1:8080**

## Usage

1. Open the dashboard at `http://127.0.0.1:8080`
2. Paste a `.md` file path in the sidebar input and click **+ Track File**
3. Click a file card to open the viewer
4. Tick checkboxes as you complete steps
5. Return to dashboard to see overall progress across all files

## Project Structure

```
md-tracker/
├── app/
│   ├── main.py              # FastAPI routes
│   ├── database.py           # SQLite CRUD
│   ├── parser.py             # MD step extraction
│   ├── config.py             # Configuration
│   ├── templates/
│   │   ├── base.html         # Sidebar layout
│   │   ├── dashboard.html    # Dashboard + charts
│   │   └── viewer.html       # MD viewer + checkboxes
│   └── static/
│       ├── style.css         # All styles
│       └── app.js            # Frontend logic
├── requirements.txt
├── setup.ps1
├── launch.bat
└── README.md
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard |
| GET | `/view/{file_id}` | Viewer page |
| POST | `/api/files` | Add file to tracking |
| GET | `/api/files` | List all tracked files |
| DELETE | `/api/files/{id}` | Remove file |
| GET | `/api/files/{id}/steps` | Get steps for file |
| PATCH | `/api/steps/{id}` | Toggle step completion |
| POST | `/api/files/{id}/rescan` | Re-parse file |
| GET | `/api/stats` | Global stats |

## Tech Stack

- **Python 3.11+** / FastAPI
- **SQLite** (persistent, file-based)
- **Jinja2** templates
- **Chart.js** (dashboard charts)
- **marked.js** (markdown rendering)
