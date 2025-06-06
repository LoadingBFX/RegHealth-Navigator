# 🏥 RegHealth Navigator

**Authors:**  
Xiao Yan, Dhruv Tangri, Sarvesh Siras, Saicharan Emmadi, Seon Young Jhang, Fanxing Bu

**Last Updated:** March 2024  
**Status:** 🚧 In Development

[![Capstone Project](https://img.shields.io/badge/CMU-Capstone%20Project-red)](https://www.cmu.edu/)

## 📖 Project Introduction

RegHealth Navigator is an intelligent regulatory document analysis platform designed to help healthcare professionals, compliance officers, and policy analysts efficiently understand and analyze complex Medicare regulations. The system provides powerful tools for document comparison, semantic search, and AI-powered analysis.

## ✨ Key Features

### 1. Document Management
- **Standardized File Organization**
  - Format: `{year}_{program_type}_{type}_{document_number}`
  - Example: `2024_MPFS_final_2024-14828`
  - Program Types: MPFS, HOSPICE, SNF
  - Document Types: final, proposed

### 2. Smart Analysis Tools
- **Document Comparison**
  - Side-by-side document comparison
  - Color-coded change tracking:
    - 🟢 Green: Added content
    - 🔴 Red: Removed content
    - 🟡 Yellow: Modified content
  - Expandable sections for detailed review

- **AI-Powered Features**
  - Smart document summarization
  - FAQ generation
  - Key points extraction
  - Context-aware chat assistance

### 3. User Interface
- **Modern Design**
  - Clean, intuitive interface
  - Responsive layout
  - Dark/light mode support
  - Accessible components

- **Interactive Features**
  - Real-time document search
  - Citation system with modal view
  - Chat history management
  - Document selection interface

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.9+
- npm or yarn

### Frontend Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/LoadingBFX/RegHealth-Navigator.git
   cd RegHealth-Navigator
   ```

2. **Install dependencies**
   ```bash
   cd front
   npm install
   ```

3. **Start development server**
   ```bash
   npm run dev
   ```
   The application will be available at http://localhost:5173

### Backend Setup

1. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start the server**
   ```bash
   uvicorn app.main:app --reload
   ```

## 📥 Document Download Instructions

1. **Access Document Library**
   - Click on the document selector in any tab
   - Use the search bar to find specific documents
   - Filter by year, program type, and document type

2. **Download Process**
   - Select the desired document(s)
   - Click the download button
   - Documents will be saved in your default download location

3. **File Organization**
   - Downloaded files follow the standard naming convention
   - Store in a dedicated folder for easy access
   - Use the application's file selector to load local documents

## 🛠️ Development

### Tech Stack
- **Frontend**
  - React 18
  - TypeScript
  - Tailwind CSS
  - Vite
  - Zustand (State Management)

- **Backend**
  - Python 3.9+
  - FastAPI
  - SQLAlchemy
  - PostgreSQL
  - Redis (for caching)

### Project Structure
```
RegHealth-Navigator/
├── front/                 # Frontend React application
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── store/       # State management
│   │   └── types/       # TypeScript types
│   └── public/          # Static assets
│
├── backend/              # Python FastAPI application
│   ├── app/
│   │   ├── api/        # API endpoints
│   │   ├── core/       # Core functionality
│   │   └── models/     # Database models
│   └── tests/          # Test suite
│
└── docs/                # Documentation
    ├── api/            # API documentation
    └── guides/         # Development guides
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Medicare.gov for regulation data
- OpenAI for AI capabilities
- All contributors and maintainers
