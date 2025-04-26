
# 🩺 RegHealth Navigator

**RegHealth Navigator** is an interactive Streamlit-based web application that helps healthcare professionals, compliance teams, and policy analysts explore, compare, and extract insights from U.S. healthcare regulatory documents (e.g., CMS proposed and final rules). It uses Retrieval-Augmented Generation (RAG) with OpenAI models.

---

## 🚀 Features

### 1. 💬 Ask Questions
- Ask free-text questions about healthcare rules.
- Automatically retrieves the most relevant rule sections.
- Generates a GPT-based answer and simplified summary.
- Optional metadata filters (Program, Year, Rule Type).
- Mismatch warnings between query and filters.

### 2. 📊 Compare Rules
- Compare any two rules by year, version, program, or section.
- Summarizes key differences and implications.
- Validates input filters with GPT-enhanced clarification.
- Displays matched context with optional preview.

### 3. 📈 Generate Insights
- Describe a policy scenario (e.g., 2025 SNF final rule on payment updates).
- GPT generates strategic guidance based on retrieved rule content.
- Outputs structured, actionable recommendations.
- Metadata filters and mismatch safeguards supported.

### 4. 📚 Document Explorer
- Filter documents by Program, Year, and Rule Type.
- Search for relevant sections based on a user prompt.
- View formatted section text and metadata.

### 5. 🧠 Session History
- View all queries and results from the current session.
- Organized by query type (Ask, Compare, Insight).
- Display raw GPT responses and used context.

---

## 📂 Folder Structure

```
.
├── app.py                     # Launch screen + OpenAI setup
├── pages/
│   ├── 1_💬_Ask_Questions.py
│   ├── 2_📊_Compare_Rules.py
│   ├── 3_📈_Generate_Insights.py
│   ├── 4_📚_Document_Explorer.py
│   └── 5_🧠_History.py
├── state.py                   # Shared app logic (RAG, filters, tokenizer)
├── rag_data/                  # Folder for FAISS index and metadata
│   ├── faiss.index
│   ├── faiss_metadata.json
├── data/                      # Folder for original XML rule files
│   └── *.xml
├── xml_process.ipynb         # Script to parse XML and create chunks.json
├── build_faiss_from_chunks.ipynb  # Script to embed and build FAISS index
```

---

## 🧰 Setup Instructions

1. **Install Requirements**:
```bash
pip install -r requirements.txt
```

2. **Prepare XML Data**:
- Place CMS rule XML files into the `data/` folder.

3. **Run Preprocessing**:
- Open `xml_process.ipynb` and run to generate `chunks.json`.
- Open `build_faiss_from_chunks.ipynb` to generate `rag_data/faiss.index` and `faiss_metadata.json`.

4. **Run the App**:
```bash
streamlit run Home.py
```

---

## 🔐 Security

- The app requires user input of an OpenAI API key.
- No data is stored or shared externally.
- Local-only history is stored in `st.session_state`.

---

## 🧠 Model Support

- ✅ GPT-4o (default): Fast and cost-effective with 128k token support.
- ❌ GPT-4: Removed to avoid context-length issues.

---

## ✨ Credits

Built with ❤️ by Huating Sun for graduate research in HCI + healthcare AI policy.
