import os
from pathlib import Path
from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain_classic.chains import create_retrieval_chain
from langchain_classic.chains.combine_documents import create_stuff_documents_chain

_embeddings = None
_BASE = Path(os.getcwd()) / "vector_store"
_BASE.mkdir(exist_ok=True)

_HISTORY: dict[str, list] = {}


def _emb():
    global _embeddings
    if _embeddings is None:
        _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return _embeddings


def _store_path(session_id: str) -> Path:
    p = _BASE / session_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def _grade(marks: int) -> tuple[str, int]:
    if marks >= 90: return "S", 10
    if marks >= 80: return "A", 9
    if marks >= 70: return "B", 8
    if marks >= 60: return "C", 7
    if marks >= 55: return "D", 6
    if marks >= 50: return "E", 5
    if marks >= 40: return "P", 4
    return "F", 0


def _docs(subject_data, context_subjects, scheme, semester, branch):
    credit_lookup = {s["SubjectCode"].upper(): s["SubjectCredits"] for s in (context_subjects or [])}
    docs = []
    total_marks = 0
    passed = 0
    weighted_points = 0.0
    total_credits = 0.0

    for item in subject_data:
        code = str(item.get("code", "")).upper()
        # Extract the subject name so the bot remembers it!
        name = str(item.get("subject_name", "")).strip() or str(item.get("name", "")).strip() or "Unknown Subject"
        marks = int(item.get("total_marks", 0))
        status = "Passed" if item.get("status") == "P" else "Failed"
        credits = credit_lookup.get(code)
        grade, gp = _grade(marks)

        total_marks += marks
        if status == "Passed":
            passed += 1
        if credits:
            weighted_points += gp * credits
            total_credits += credits

        # Added the subject name into the text chunk that gets vectorized
        parts = [
            f"Subject {code} ({name}): scored {marks}/100",
            f"grade {grade} (grade point {gp})",
            f"result {status}",
        ]
        if credits:
            parts.append(f"worth {credits} credits")
        if scheme and semester and branch:
            parts.append(f"in {branch} scheme {scheme} semester {semester}")

        docs.append(Document(
            page_content=". ".join(parts) + ".",
            metadata={
                "subject_code": code,
                "subject_name": name, # Saved to metadata as well
                "marks": marks, 
                "status": status,
                "grade": grade, 
                "grade_point": gp, 
                "credits": credits or 0,
                "scheme": scheme or "", 
                "semester": semester or "", 
                "branch": branch or "",
            },
        ))

    n = len(subject_data) or 1
    avg = round(total_marks / n, 2)
    sgpa = round(weighted_points / total_credits, 2) if total_credits else None
    summary = (
        f"Overall summary: {len(subject_data)} subjects, {passed} passed, "
        f"{len(subject_data) - passed} failed. Average marks {avg}/100."
    )
    if sgpa is not None:
        summary += f" Computed SGPA {sgpa}."
    docs.append(Document(page_content=summary, metadata={"kind": "summary"}))
    return docs

def build_vector_store(subject_data, session_id: str, context_subjects=None,
                       scheme=None, semester=None, branch=None):
    docs = _docs(subject_data, context_subjects, scheme, semester, branch)
    if not docs:
        return None
    store = FAISS.from_documents(docs, _emb())
    store.save_local(str(_store_path(session_id)))
    _HISTORY[session_id] = []  # reset chat on new upload
    return store

def clear_history(session_id: str):
    """Clears the conversational memory for a given user session."""
    if session_id in _HISTORY:
        _HISTORY[session_id] = []


def query_marksheet(question: str, groq_api_key: str, session_id: str,
                    model: str = "llama-3.1-8b-instant") -> str:
    path = _store_path(session_id)
    if not (path / "index.faiss").exists():
        return "Upload your marksheet first — I don't have any data for this session yet."

    store = FAISS.load_local(str(path), _emb(), allow_dangerous_deserialization=True)
    # INCREASE k to 25 so it ALWAYS loads all subjects into memory, ignoring minor typos!
    retriever = store.as_retriever(search_kwargs={"k": 25})

    llm = ChatGroq(groq_api_key=groq_api_key, model_name=model, temperature=0.3) 
    
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are an encouraging and helpful VTU academic assistant. \n"
         "1. CRITICAL PRIORITY: If the student asks for advice on how to achieve a certain CGPA/SGPA, improve grades, or study tips, you MUST provide a detailed, actionable bulleted plan using your general knowledge. Provide this advice clearly and fully.\n"
         "2. For purely factual questions about their extracted grades, answer naturally. DO NOT use the word 'context'.\n"
         "3. IMPORTANT: DO NOT append the user's marks or UI calculator warning UNLESS they explicitly ask for their current grades or CGPA. For advice, ONLY provide the advice.\n\n"
         "VTU Slang / Subject Abbreviations to recognize (Map these if the user asks):\n"
         "- OS: Operating Systems\n"
         "- DSA / DS: Data Structures\n"
         "- CN: Computer Networks\n"
         "- DBMS: Database Management Systems\n"
         "- AIML / ML / AI: Machine Learning or Artificial Intelligence\n"
         "- M1 / M2 / M3 / M4: Engineering Mathematics\n"
         "- COA: Computer Organization and Architecture\n"
         "- ATC / TOC: Automata Theory and Computability\n\n"
         "Knowledge Base:\n{context}"),
        MessagesPlaceholder("history"),
        ("human", "{input}"),
    ])
    chain = create_retrieval_chain(retriever, create_stuff_documents_chain(llm, prompt))

    history = _HISTORY.setdefault(session_id, [])
    result = chain.invoke({"input": question, "history": history})
    answer = result["answer"]

    history.append(HumanMessage(content=question))
    history.append(AIMessage(content=answer))
    _HISTORY[session_id] = history[-12:]  # cap
    return answer