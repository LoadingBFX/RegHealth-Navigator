# RegHealth Navigator

RegHealth Navigator is a fullstack application for regulatory professionals to quickly analyze, summarize, and compare large XML documents (e.g., health-tech, pharma, clinical research). It features a modern chat-based UI, mind-maps, and change-tracking, with a scalable backend for high-volume XML processing.

---

## Features
- Upload, search, and select large XML files (200MB+)
- Fast, streaming XML parsing and chunking
- Interactive mind-map and summary generation
- Contextual Q&A chat with inline citations
- Document comparison and change-tracking
- Caching for instant re-use of processed artefacts

---

## Requirements
- **Node.js**: v20+ (recommended: use [nvm](https://github.com/nvm-sh/nvm))
- **Python**: 3.10+
- **Poetry** (optional, for advanced Python dependency management)
- **Redis** (for caching, optional for local dev)

---

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/reghealth-navigator.git
cd reghealth-navigator
```

### 2. Install Node.js (with nvm)
```bash
nvm install 20
nvm use 20
```

### 3. Install Frontend Dependencies
```bash
cd front
npm install
```

### 4. Install Python Dependencies
```bash
cd ..
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. Environment Variables
Copy `.env.example` to `.env` and fill in required values (API keys, etc).

---

## Running the Project

### 1. Start the Backend (FastAPI)
```bash
uvicorn app.main:app --reload
```

### 2. Start the Frontend (Vite/React)
```bash
cd front
npm run dev
```

The frontend will be available at `http://localhost:5173` and the backend at `http://localhost:8000` by default.

---

## Development Workflow
- Use feature branches from `dev` for all new work
- Open Pull Requests (PR) to `dev` branch
- Ensure all tests pass and code is reviewed before merging
- Use clear commit messages and PR descriptions
- See `GITHUB_WORKFLOW.md` for detailed workflow

---

## Testing
- **Frontend:**
  ```bash
  cd front
  npm run test
  ```
- **Backend:**
  ```bash
  pytest
  ```

---

## Scripts
All experimental and data analysis scripts are in the `scripts/` folder. Example:
- `scripts/xml_structure_analysis.py` — Analyze XML structure
- `scripts/xml_token_count.py` — Count tokens/words in XML

---

## Contact
For questions or contributions, open an issue or contact the maintainers. 