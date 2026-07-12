document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".sgpa-input").forEach(i => i.addEventListener("input", recalc));
  document.getElementById("resetBtn").addEventListener("click", () => {
    document.querySelectorAll(".sgpa-input").forEach(i => i.value = ""); recalc();
  });
  document.querySelectorAll("#schemeGroup button").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll("#schemeGroup button").forEach(x => x.classList.remove("bg-white","shadow"));
    b.classList.add("bg-white","shadow");
  }));
});

function recalc() {
  let sum = 0, n = 0;
  for (let i = 1; i <= 8; i++) {
    const v = parseFloat(document.getElementById("sem" + i).value);
    if (!isNaN(v) && v > 0) { sum += v; n++; }
  }
  const el = document.getElementById("cgpaValue");
  const br = document.getElementById("cgpaBreak");
  const pct = document.getElementById("pctValue");
  if (n === 0) { el.textContent = "—"; br.textContent = "Fill in any semester to start."; pct.textContent = "—"; return; }
  const cgpa = sum / n;
  el.textContent = cgpa.toFixed(2);
  br.textContent = `Average of ${n} semester${n>1?"s":""}`;
  pct.textContent = (cgpa * 9.5).toFixed(2) + "%";
}
