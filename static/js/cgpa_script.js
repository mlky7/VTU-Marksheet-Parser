function calculateCGPA() {
  const semesters = 8;
  let totalSGPA = 0;
  let count = 0;

  for (let i = 1; i <= semesters; i++) {
    const sgpa = parseFloat(document.getElementById(`sem${i}`).value) || 0;
    totalSGPA += sgpa;
    if (sgpa > 0) count++;
  }

  const cgpa = count > 0 ? (totalSGPA / count).toFixed(2) : 0;
  document.getElementById("resultDisplay").textContent = `CGPA: ${cgpa}`;
}

function resetFields() {
  for (let i = 1; i <= 8; i++) {
    document.getElementById(`sem${i}`).value = "";
  }
  document.getElementById("resultDisplay").textContent = "";
}
