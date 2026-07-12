# VTU Marksheet Parser & Academic Assistant

Flask app that parses VTU marksheets (PDF), auto-fills SGPA/CGPA calculators,
and offers a per-session RAG chat over your extracted marks.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env      # paste your GROQ_API_KEY
python app.py
```

Open http://127.0.0.1:5000

## Notes

- The Groq API key is read from `.env` — do not commit real keys.
- Uploads are `.pdf` only, capped at 10 MB.
- Each browser session gets its own FAISS vector store under
  `vector_store/<session_id>/` so users never see each other's data.
- If the regex parser finds nothing in your PDF, the app falls back to
  an LLM-based extractor (`parser.py`).
