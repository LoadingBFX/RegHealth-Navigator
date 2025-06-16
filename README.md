# 🏥 RegHealth Navigator

**Authors:**  
Xiao Yan, Dhruv Tangri, Sarvesh Siras, Saicharan Emmadi, Seon Young Jhang, Fanxing Bu

**Last Updated:** March 2025
**Status:** 🚧 In Development

[![Capstone Project](https://img.shields.io/badge/CMU-Capstone%20Project-red)](https://www.cmu.edu/)

---

## 📖 Project Introduction

RegHealth Navigator is an intelligent regulatory document analysis platform designed to help healthcare professionals, compliance officers, and policy analysts efficiently understand and analyze complex Medicare regulations. The system provides powerful tools for document comparison, semantic search, and AI-powered analysis.

---

## 📁 Project Structure
```
RegHealth-Navigator/
├── app/                  # Backend Flask application
│   ├── core/             # Core backend logic (RAG, search, etc.)
│   ├── config/           # YAML config files for environment/resource paths
│   └── main.py           # Flask entry point
│   └── ...               # (other backend modules)
│
├── front/                # Frontend React application
│   ├── src/
│   └── ...               # (components, store, etc.)
│
├── rag_data/             # FAISS index and metadata files (not in git)
│
├── docs/                 # Documentation
│
├── .env                  # Backend sensitive config (not committed)
├── requirements.txt      # Backend dependencies
└── README.md
```

---

## ⚙️ Configuration & Environment Variables

### Backend
- **.env**: Stores sensitive info (e.g., `OPENAI_API_KEY`). Not committed. See `.env.example` for template.
- **app/config/*.yml**: Stores resource paths, CORS, and other environment-specific settings. See example files.
- **rag_data/**: Stores FAISS index and metadata files. Not committed.

**Example: Loading API key from .env in Python**
```python
from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")
```

### Frontend
- **front/.env.development**, **front/.env.production**: Store API base URL and feature flags. See `front/.env.example` for required variables.

**Example: Accessing API URL in React/Vite**
```typescript
const apiUrl = import.meta.env.VITE_API_BASE_URL;
```

---

## 🚀 Backend Setup (Flask)
1. Copy `.env.example` to `.env` and fill in your OpenAI API key.
2. Copy `app/config/development.yml.example` to `app/config/development.yml` and adjust paths if needed.
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start the Flask server:
   ```bash
   export FLASK_APP=app/main.py
   export FLASK_ENV=development
   export FLASK_APP=app.main:create_app
   flask run --host=127.0.0.1 --port=8080
   ```

---

## 🚀 Frontend Setup
1. Copy `front/.env.example` to `front/.env.development` and set the backend API URL.
2. Install dependencies and run:
   ```bash
   cd front
   npm install
   npm run dev
   ```

---

## 🤝 Team Collaboration & Best Practices
- Do **not** commit `.env`, `rag_data/`, or actual config files to git. Only commit `.example` templates.
- All resource paths and sensitive info are managed via config and env files for security and flexibility.
- New developers should always start by copying `.env.example` and config example files.

---

## ❓ FAQ / Troubleshooting
- **Q: API key not set error?**
  - A: Check your `.env` file and ensure `OPENAI_API_KEY` is set and has no extra spaces.
- **Q: rag_data path error?**
  - A: Check `app/config/development.yml` for correct paths and ensure `rag_data/` exists.
- **Q: Frontend cannot connect to backend?**
  - A: Check `VITE_API_BASE_URL` in your frontend env file and CORS settings in backend config.

---

## 📝 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- Medicare.gov for regulation data
- OpenAI for AI capabilities
- All contributors and maintainers
