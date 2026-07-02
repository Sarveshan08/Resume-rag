# 📄 ResuMind RAG — AI Resume Analyzer & Builder

> **A powerful Retrieval-Augmented Generation (RAG) powered resume analyzer, ATS scorer, and intelligent resume builder that replicates professional resume layouts with AI-driven content optimization.**

[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.x-red?style=flat-square&logo=streamlit)](https://streamlit.io)
[![Groq](https://img.shields.io/badge/Groq-LLaMA_3.3_70B-orange?style=flat-square)](https://console.groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_DB-green?style=flat-square)](https://www.trychroma.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)](LICENSE)

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 **ATS Scorecard** | Deep resume analysis with scores across formatting, language, impact, and relevance |
| 🎯 **JD Gap Analyzer** | Semantic RAG-powered comparison between your resume and any job description |
| ✏️ **Resume Builder** | Edit all resume sections in a structured form and export as a beautiful HTML/PDF |
| 💬 **Hybrid Q&A Chat** | Ask resume questions (RAG-sourced) or career advice scenarios (LLM general knowledge) |
| ⚡ **STAR Optimizer** | Rewrite weak bullet points using the STAR method and apply them directly to your resume |
| 🏆 **Hackathons Section** | Dedicated section to showcase competitions and awards |
| 🖨️ **Print-Ready PDF** | One-click browser print to generate a clean, ATS-optimized vector PDF |

---

## 🖥️ Demo

![ResuMind Demo](https://raw.githubusercontent.com/Sarveshan08/Resume-rag/main/assets/demo_screenshot.png)

---

## 🏗️ Architecture

```
📄 PDF Upload
      │
      ▼
 pypdf (Text Extraction)
      │
      ▼
 ChromaDB (In-Memory Vector Store) ◄──► SentenceTransformers (all-MiniLM-L6-v2)
      │
      ▼
 Groq LLM API (LLaMA 3.3 70B)
      │
      ├──► ATS Scorecard
      ├──► JD Gap Analysis
      ├──► Hybrid Q&A Chat
      ├──► STAR Bullet Optimizer
      └──► JSON Resume Parser ──► HTML Template Builder ──► PDF Export
```

---

## 📁 Project Structure

```
Resume-rag/
│
├── app.py              # Main Streamlit frontend & UI logic
├── rag_engine.py       # RAG pipeline: extraction, embeddings, ChromaDB, Groq client
├── prompts.py          # All LLM system prompts (Summary, ATS, QA, STAR, JSON Parser)
├── templates.py        # HTML/CSS resume templates (Classic Minimalist & Modern Sidebar)
├── requirements.txt    # Python dependencies
├── .gitignore          # Excludes secrets, cache, and local DB files
└── .streamlit/
    └── secrets.toml    # 🔒 Local only — NEVER committed to GitHub
```

---

## 🚀 Getting Started (Local)

### 1. Clone the repository
```bash
git clone https://github.com/Sarveshan08/Resume-rag.git
cd Resume-rag
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Set up your Groq API Key
Get a free API key at [console.groq.com](https://console.groq.com), then create a local secrets file:
```bash
mkdir .streamlit
```
Create `.streamlit/secrets.toml` and add:
```toml
GROQ_API_KEY = "your_gsk_key_here"
```

### 4. Run the app
```bash
python -m streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. Fork this repository to your GitHub account.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **"New app"** → select this repo → set main file to `app.py`.
4. Under **Advanced Settings → Secrets**, add:
   ```toml
   GROQ_API_KEY = "your_gsk_key_here"
   ```
5. Click **Deploy** — your app will be live in ~3 minutes!

---

## 📦 Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit (glassmorphic dark theme, custom CSS) |
| **LLM** | Groq API — LLaMA 3.3 70B Versatile |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` (local, offline) |
| **Vector Store** | ChromaDB (EphemeralClient — in-memory, session-isolated) |
| **PDF Parsing** | pypdf |
| **Resume Templates** | Custom HTML/CSS (Classic Minimalist & Modern Sidebar) |

---

## 💡 How to Export as PDF

1. Go to the **Resume Builder & PDF Export** tab.
2. Edit your details in the structured form.
3. Select a template layout (**Classic Minimalist** recommended for ATS).
4. Click **"Download HTML Resume"**.
5. Open the downloaded `.html` file in **Chrome or Edge**.
6. Press **`Ctrl + P`** → Set destination to **"Save as PDF"** → Check **"Background graphics"** → Save.

> ⚠️ **Important:** Do NOT use "Microsoft Print to PDF" — it rasterizes text into an image, making it unreadable by ATS systems. Always use the browser's built-in **"Save as PDF"** option.

---

## 🔒 Privacy & Security

- **API keys** are loaded from Streamlit Secrets or a local `.streamlit/secrets.toml` file. They are **never hardcoded** in the source code.
- **Resume data** is stored in an in-memory ChromaDB instance, isolated per user session. No data is written to disk or persisted between sessions.
- **Hugging Face embeddings** are downloaded once and cached locally. Anonymous download is enforced to avoid token authentication errors.

---

## 📝 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙌 Acknowledgements

- [Groq](https://groq.com) for blazing-fast LLM inference
- [Streamlit](https://streamlit.io) for the rapid web app framework
- [ChromaDB](https://www.trychroma.com) for the vector database
- [Sentence Transformers](https://www.sbert.net) for local semantic embeddings
