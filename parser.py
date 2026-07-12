import json
import re
import pdfplumber

# FIXED: We added a capture group `([^\d]+?)` to actually save the Subject Name
SUBJECT_RE = re.compile(
    r"(\b[A-Z]{2,5}\d{2,3}[A-Z]?\d?[A-Z]?\b)\s+([^\d]+?)\s+(\d{1,3})\s+(\d{1,3})\s+(\d{1,3})\s+([PF])"
)

def _read_pdf_text(path: str) -> str:
    text = ""
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            text += (p.extract_text() or "") + "\n"
    return text

def _regex_extract(text: str):
    matches = SUBJECT_RE.findall(text)
    return [
        {
            "code": m[0].strip(),
            "subject_name": m[1].strip(),       # NEW: Now we actually save the name!
            "total_marks": int(m[4]),           # Shifted to index 4 because we added the name group
            "status": m[5].strip()
        }
        for m in matches
    ]

def _llm_extract(text: str, groq_api_key: str, model: str):
    """Fallback: ask an LLM to structure the marks."""
    from langchain_groq import ChatGroq
    from langchain_core.prompts import ChatPromptTemplate

    llm = ChatGroq(groq_api_key=groq_api_key, model_name=model, temperature=0)
    
    # FIXED: Added `"subject_name": "<subject name>"` to the JSON schema instructions
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Extract every subject row from this VTU marksheet text. "
         "Return ONLY a JSON array. Each item: "
         '{"code": "<subject code>", "subject_name": "<subject name>", "total_marks": <int 0-100>, "status": "P" or "F"}. '
         "No prose, no code fences."),
        ("human", "{text}"),
    ])
    raw = (prompt | llm).invoke({"text": text[:12000]}).content.strip()
    
    # FIXED: Using chr(96) to generate backticks dynamically so the chat UI doesn't cut off the code block!
    bt = chr(96)
    pattern = f"^{bt}{{3}}(?:json)?|{bt}{{3}}$"
    raw = re.sub(pattern, "", raw, flags=re.MULTILINE).strip()
    
    try:
        data = json.loads(raw)
        clean = []
        for item in data:
            code = str(item.get("code", "")).strip().upper()
            name = str(item.get("subject_name", "")).strip()
            marks = int(item.get("total_marks", 0))
            status = str(item.get("status", "P")).strip().upper()[:1]
            if code and status in ("P", "F"):
                clean.append({
                    "code": code, 
                    "subject_name": name if name else "Unknown Subject", 
                    "total_marks": marks, 
                    "status": status
                })
        return clean
    except Exception:
        return []

def extract_subject_data(pdf_path: str, groq_api_key: str | None = None,
                         groq_model: str = "llama-3.1-8b-instant"):
    text = _read_pdf_text(pdf_path)
    data = _regex_extract(text)
    if data or not groq_api_key:
        return data
    return _llm_extract(text, groq_api_key, groq_model)