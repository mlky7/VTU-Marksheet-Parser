const $ = (s) => document.querySelector(s);
const gradeOf = (m) => {
  m = parseFloat(m);
  if (isNaN(m)) return { g: "-", gp: 0 };
  if (m >= 90) return { g: "S", gp: 10 }; if (m >= 80) return { g: "A", gp: 9 };
  if (m >= 70) return { g: "B", gp: 8 };  if (m >= 60) return { g: "C", gp: 7 };
  if (m >= 55) return { g: "D", gp: 6 };  if (m >= 50) return { g: "E", gp: 5 };
  if (m >= 40) return { g: "P", gp: 4 };  return { g: "F", gp: 0 };
};

document.addEventListener("DOMContentLoaded", () => {
  ["scheme", "semester", "branch"].forEach(id => $("#" + id).addEventListener("change", loadSubjects));
  $("#fileInput").addEventListener("change", (e) => {
    const f = e.target.files[0]; $("#fileName").textContent = f ? f.name : "";
  });
  const drop = $("#drop");
  ["dragover","dragenter"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.add("border-brand-500","bg-brand-50/60"); }));
  ["dragleave","drop"].forEach(ev => drop.addEventListener(ev, e => { e.preventDefault(); drop.classList.remove("border-brand-500","bg-brand-50/60"); }));
  drop.addEventListener("drop", e => {
    const f = e.dataTransfer.files[0]; if (!f) return;
    $("#fileInput").files = e.dataTransfer.files; $("#fileName").textContent = f.name;
  });
  $("#uploadForm").addEventListener("submit", handleUpload);
  loadSubjects();
});

async function loadSubjects() {
  const scheme = $("#scheme").value, semester = $("#semester").value, branch = $("#branch").value;
  const body = $("#subjectsTableBody"); body.innerHTML = "";
  if (!scheme || semester === "#" || !branch) return recalc();
  const r = await fetch(`/get_subjects?scheme=${scheme}&semester=${encodeURIComponent(semester)}&branch=${branch}`);
  const data = await r.json();
  if (!Array.isArray(data)) return;
  data.forEach(sub => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="px-4 py-2 font-semibold">${sub.SubjectCode}</td>
      <td class="px-4 py-2">${sub.SubjectCredits}</td>
      <td class="px-4 py-2"><input type="number" min="0" max="100" class="marks w-24 rounded-md border border-ink-300 px-2 py-1 focus:ring-2 focus:ring-brand-500 outline-none" data-credits="${sub.SubjectCredits}"></td>
      <td class="px-4 py-2"><span class="grade-badge g-">-</span></td>`;
    body.appendChild(tr);
  });
  body.querySelectorAll("input.marks").forEach(i => i.addEventListener("input", recalc));
  recalc();
}

async function handleUpload(e) {
  e.preventDefault();
  const f = $("#fileInput").files[0];
  if (!f) { $("#uploadStatus").textContent = "Pick a PDF first."; return; }
  const btn = $("#uploadBtn"); btn.disabled = true;
  $("#uploadStatus").textContent = "Extracting…";
  const fd = new FormData();
  fd.append("file", f);
  fd.append("scheme", $("#scheme").value);
  fd.append("semester", $("#semester").value);
  fd.append("branch", $("#branch").value);
  try {
    const r = await fetch("/upload", { method: "POST", body: fd });
    const data = await r.json();
    if (!r.ok) throw new Error(data.error || "Upload failed");
    fillChips(data); fillMarks(data);
    $("#uploadStatus").innerHTML = `<span class="text-emerald-600 font-semibold">✓ Extracted ${data.length} subjects</span>`;
  } catch (err) {
    $("#uploadStatus").innerHTML = `<span class="text-red-600 font-semibold">${err.message}</span>`;
  } finally { btn.disabled = false; }
}

function fillChips(data) {
  const c = $("#chips"); c.innerHTML = "";
  data.forEach(d => {
    const s = document.createElement("span");
    s.className = "chip"; s.textContent = `${d.code} · ${d.total_marks}`;
    if (d.status === "F") { s.style.background = "#fee2e2"; s.style.color = "#b91c1c"; }
    c.appendChild(s);
  });
}

function fillMarks(data) {
  const rows = $("#subjectsTableBody").querySelectorAll("tr");
  const map = new Map(data.map(d => [d.code.toUpperCase(), d.total_marks]));
  rows.forEach(row => {
    const code = row.cells[0].textContent.trim().toUpperCase();
    if (map.has(code)) row.querySelector("input.marks").value = map.get(code);
  });
  recalc();
}

function recalc() {
  let cr = 0, pts = 0;
  $("#subjectsTableBody").querySelectorAll("tr").forEach(row => {
    const input = row.querySelector("input.marks");
    const badge = row.querySelector(".grade-badge");
    const credits = parseFloat(input.dataset.credits) || 0;
    const { g, gp } = gradeOf(input.value);
    badge.textContent = g; badge.className = "grade-badge g-" + g;
    if (input.value !== "") { cr += credits; pts += gp * credits; }
  });
  $("#totalCredits").textContent = cr;
  $("#totalPoints").textContent = pts.toFixed(1);
  if (cr > 0) {
    const sgpa = (pts / cr).toFixed(2);
    $("#sgpaValue").textContent = sgpa;
    $("#sgpaBreak").textContent = `${pts.toFixed(1)} points ÷ ${cr} credits`;
  } else {
    $("#sgpaValue").textContent = "—";
    $("#sgpaBreak").textContent = "Enter marks to see live SGPA.";
  }
}
