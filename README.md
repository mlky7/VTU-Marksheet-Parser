# VTU Marksheet Parser & AI Assistant

A web-based application that allows users to upload their VTU mark sheets in PDF format, automatically extracts marks, and fills the SGPA calculator input fields. The application also features a conversational AI assistant (RAG pipeline) that answers questions about the student's grades and provides academic advice. 

The extracted data (marks, credits, and subject names) is mapped to official curriculum guidelines, CSE semesters of the 2022 scheme (for now), with potential for additional semesters and subjects in the future.

### Features

* **Upload VTU Marksheet:** Users can upload their VTU marksheet in PDF format through the main dashboard or directly inside the AI chat interface.
* **Automatic Mark Extraction:** The parser utilizes a hybrid approach, using `pdfplumber` (Regex) for fast extraction with an LLM fallback, to read marks, grades, and subject names directly from the PDF.
* **SGPA Auto-Fill & Calculation:** Extracted marks are instantly mapped to the respective subject codes, filling the dynamic SGPA calculator automatically without manual entry.
* **CGPA Calculation Page:** Users can also compute their cumulative GPA (CGPA) across multiple semesters.
* **Interactive AI Assistant (RAG):** Features a chatbot with conversational memory powered by a FAISS vector database, allowing students to ask questions about their performance, passing criteria, and receive actionable study advice.
* **Flask Backend:** The project runs on a robust Flask server, handling PDF parsing, vector database embeddings, and API routing.

### Tech Stack

* **Backend:** Flask, Python, pdfplumber
* **AI & NLP:** LangChain, FAISS (Vector Store), HuggingFace Embeddings, Groq API (Llama-3.1)
* **Frontend:** HTML, Tailwind CSS, Vanilla JavaScript (`marked.js` for markdown rendering)
* **Database/Storage:** Local CSV mapping and FAISS Vector indexing

---

## Quick Start

To run this project locally on your machine, follow these steps:

```bash
# 1. Install required dependencies
pip install -r requirements.txt

# 2. Set up your environment variables
cp .env.example .env      # Open this file and paste your GROQ_API_KEY

# 3. Start the Flask server
python app.py
```
