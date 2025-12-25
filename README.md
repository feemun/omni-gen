# OmniGen

This project is a **Full-Stack AI Code Generator** (OmniGen) that allows you to inspect various data sources (Database, Redis, Elasticsearch) and generate code based on customizable templates.

It consists of two main parts:
- **Backend**: Python (FastAPI) + SQLAlchemy + Jinja2
- **Frontend**: Vue 3 + Vite

## Project Structure

```
omini-gen/
├── backend/          # FastAPI Backend
│   ├── app/          # Application Logic
│   └── generator_templates/ # Code Templates
├── frontend/         # Vue 3 Frontend
│   ├── src/
│   └── public/
└── README.md
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- `uv` (Python package manager)

## Setup & Run

### 1. Start Backend

Navigate to the `backend` directory and run:

```bash
cd backend
# Install dependencies
uv sync
# Run Server
uv run uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`.

### 2. Start Frontend

Navigate to the `frontend` directory and run:

```bash
cd frontend
# Install dependencies
npm install
# Run Dev Server
npm run dev
```

The UI will be available at `http://localhost:5173` (or the port shown in terminal).

## Usage

1. Open the Frontend URL.
2. Enter your Database Connection URL (e.g., `sqlite:///../backend/test.db`).
   - Note: For SQLite, the path is relative to where the *backend* process is running.
3. Click "Connect".
4. Select the tables you want to generate code for.
5. Select a template (e.g., `java/entity.java.jinja2`).
6. Click "Generate Code".

## Development

- **Add Templates**: Add `.jinja2` files to `backend/generator_templates/`.
- **Modify UI**: Edit `frontend/src/App.vue`.
