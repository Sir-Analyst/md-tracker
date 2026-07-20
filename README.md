# MD Tracker

Interactive markdown course and project progress tracker with a graphical dashboard.

## Features

- Track progress through markdown-based tutorials, courses, and project workflows
- Automatic step detection from `##` headers and numbered lists
- Interactive checkboxes to tick/untick completed steps
- Dashboard with summary cards and Chart.js progress visualization
- SQLite-backed persistent storage

## Quick Start

```powershell
# 1. Setup
.\setup.ps1

# 2. Launch
.\launch.bat
```

Then open **http://127.0.0.1:8080**

## Tech Stack

- Python 3.11+ / FastAPI
- SQLite
- Jinja2 templates
- Chart.js (dashboard charts)
- marked.js (markdown rendering)
