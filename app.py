import os
import csv
import uuid
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, request, jsonify, render_template, session
from werkzeug.utils import secure_filename

# Imported clear_history to allow wiping conversational memory
from rag import build_vector_store, query_marksheet, clear_history
from parser import extract_subject_data

load_dotenv()

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "dev-secret-change-me")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024  # 10 MB

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

BASE_DIR = Path(__file__).parent.resolve()
UPLOAD_FOLDER = BASE_DIR / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)
CSV_PATH = BASE_DIR / "subjects.csv"


def _session_id() -> str:
    if "sid" not in session:
        session["sid"] = uuid.uuid4().hex
    return session["sid"]


def _subject_rows(scheme: str, semester: str, branch: str):
    rows = []
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if (r["Scheme"].strip() == str(scheme)
                    and r["Sem"].strip() == str(semester)
                    and r["Branch"].strip() == branch):
                rows.append({
                    "SubjectCode": r["Subject Code"].strip(),
                    "SubjectCredits": float(r["Subject Credits"].strip()),
                    "SubjectName": r.get("Subject Name", "").strip() or r.get("Course Name", "").strip() or "Unknown Subject"
                })
    return rows


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/sgpa")
def sgpa():
    return render_template("sgpa.html")


@app.route("/cgpa")
def cgpa():
    return render_template("cgpa.html")


@app.route("/get_subjects", methods=["GET"])
def get_subjects():
    scheme = request.args.get("scheme")
    semester = request.args.get("semester")
    branch = request.args.get("branch")
    if not scheme or not semester or not branch:
        return jsonify({"error": "Missing parameters."}), 400
    try:
        int(scheme)
    except ValueError:
        return jsonify({"error": "Invalid scheme."}), 400
    try:
        return jsonify(_subject_rows(scheme, semester, branch))
    except FileNotFoundError:
        return jsonify({"error": "subjects.csv missing."}), 500


@app.route("/upload", methods=["POST"])
def upload_pdf():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    sid = _session_id()
    safe_name = f"{sid}_{secure_filename(file.filename)}"
    file_path = UPLOAD_FOLDER / safe_name
    file.save(file_path)

    scheme = request.form.get("scheme")
    semester = request.form.get("semester")
    branch = request.form.get("branch")
    context_subjects = []
    if scheme and semester and branch:
        try:
            context_subjects = _subject_rows(scheme, semester, branch)
        except Exception:
            context_subjects = []

    try:
        subject_data = extract_subject_data(
            str(file_path),
            groq_api_key=GROQ_API_KEY,
            groq_model=GROQ_MODEL,
        )
        if not subject_data:
            return jsonify({"error": "Could not parse any marks from the PDF."}), 422

        build_vector_store(
            subject_data,
            session_id=sid,
            context_subjects=context_subjects,
            scheme=scheme, semester=semester, branch=branch,
        )
        return jsonify(subject_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass


@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message is missing"}), 400
    if not GROQ_API_KEY:
        return jsonify({"error": "Server is missing GROQ_API_KEY."}), 500

    sid = _session_id()
    
    # 1. Base Guardrails for ALL messages to prevent infinite loops and RAG tunnel-vision
    base_instruction = (
        "[SYSTEM DIRECTION: You are a conversational, intelligent VTU Assistant. Follow these rules strictly:\n"
        "1. Keep answers short and direct.\n"
        "2. DO NOT hallucinate subject names. If the user insists the names are in the PDF, but you do not see them in your provided text context, politely explain that the text parser did not extract them.\n"
        "3. If the user asks general questions about VTU rules, passing criteria, or what a CGPA means, use your general knowledge to answer them contextually (e.g., explain that VTU typically requires a minimum CGPA of 5.0 to pass the degree).]\n\n"
    )
    
    # 2. Math-specific check
    lowered_msg = message.lower()
    is_math_query = any(keyword in lowered_msg for keyword in ["gpa", "sgpa", "cgpa", "calculate", "math", "percentage", "total"])

    if is_math_query:
        math_injection = (
            "[SYSTEM DIRECTION: DO NOT calculate or guess SGPA/CGPA yourself. "
            "List the extracted subject marks clearly and concisely. Point out to the user that their official, "
            "accurate SGPA/CGPA calculation is automatically computed and displayed on the UI form metrics.]\n\n"
        )
        final_message = base_instruction + math_injection + message
    else:
        final_message = base_instruction + message

    try:
        # 3. Send the highly structured prompt to Groq
        answer = query_marksheet(final_message, GROQ_API_KEY, session_id=sid, model=GROQ_MODEL)
        return jsonify({"response": answer})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/clear_chat", methods=["POST"])
def clear_chat_route():
    """Wipes the LLM's conversational memory for this session."""
    sid = _session_id()
    clear_history(sid)
    return jsonify({"status": "success"})


@app.errorhandler(413)
def too_large(_):
    return jsonify({"error": "File too large. Max 10 MB."}), 413


if __name__ == "__main__":
    app.run(debug=True)