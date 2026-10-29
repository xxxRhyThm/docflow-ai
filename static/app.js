let currentId = null;

async function loadDocs() {
  const res = await fetch("/api/documents");
  const docs = await res.json();
  const tbody = document.getElementById("doc-rows");
  tbody.replaceChildren(); // RC: clear without innerHTML, even for an empty string
  docs.forEach((d) => {
    // RC fix (issue 6): never build table rows with innerHTML from PDF text.
    // Vendor / filename come from untrusted PDF content and could contain
    // HTML such as <img onerror=...>. Use textContent for every data cell.
    const tr = document.createElement("tr");
    const total = d.total_amount === null || d.total_amount === undefined ? "" : d.total_amount;
    const cells = [d.id, d.original_filename, d.invoice_number || "", d.vendor || "",
      d.invoice_date || "", `${d.currency || ""} ${total}`.trim(), d.review_status];
    cells.forEach((value) => {
      const td = document.createElement("td");
      td.textContent = String(value);
      tr.appendChild(td);
    });
    const actionTd = document.createElement("td");
    const btn = document.createElement("button");
    btn.textContent = "Review";
    btn.addEventListener("click", () => openReview(d.id));
    actionTd.appendChild(btn);
    tr.appendChild(actionTd);
    tbody.appendChild(tr);
  });
}

async function openReview(id) {
  const res = await fetch(`/api/documents/${id}`);
  if (!res.ok) { alert("Document not found."); return; }
  const d = await res.json();
  currentId = d.id;
  document.getElementById("f-number").value = d.invoice_number || "";
  document.getElementById("f-vendor").value = d.vendor || "";
  document.getElementById("f-date").value = d.invoice_date || "";
  document.getElementById("f-currency").value = d.currency || "";
  document.getElementById("f-total").value = d.total_amount === null ? "" : d.total_amount;
  document.getElementById("review-warnings").textContent =
    d.warnings.length ? "Validation warnings:\n" + d.warnings.join("\n") : "No validation warnings.";
  document.getElementById("review-card").hidden = false;
  document.getElementById("review-msg").textContent = "";
}

document.getElementById("upload-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("file-input").files[0];
  const msg = document.getElementById("upload-msg");
  if (!file) { msg.textContent = "Please choose a PDF file."; return; }
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/upload", { method: "POST", body: form });
  const data = await res.json();
  if (!res.ok) { msg.textContent = "Upload failed: " + (data.detail || "unknown error"); return; }
  msg.textContent = `Uploaded as document #${data.id}. Warnings: ${data.warnings.length ? data.warnings.join("; ") : "none"}`;
  await loadDocs();
  await openReview(data.id);
});

document.getElementById("review-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const totalRaw = document.getElementById("f-total").value;
  const payload = {
    invoice_number: document.getElementById("f-number").value || null,
    vendor: document.getElementById("f-vendor").value || null,
    invoice_date: document.getElementById("f-date").value || null,
    currency: document.getElementById("f-currency").value || null,
    total_amount: totalRaw === "" ? null : Number(totalRaw),
  };
  const res = await fetch(`/api/documents/${currentId}/review`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  const data = await res.json();
  document.getElementById("review-msg").textContent =
    res.ok ? `Confirmed. Remaining warnings: ${data.warnings.length ? data.warnings.join("; ") : "none"}`
           : `Review failed: ${data.detail || "unknown error"}`;
  await loadDocs();
});

document.getElementById("refresh-btn").addEventListener("click", loadDocs);
document.getElementById("export-json-btn").addEventListener("click", () => { window.location.href = "/api/export?format=json"; });
document.getElementById("export-csv-btn").addEventListener("click", () => { window.location.href = "/api/export?format=csv"; });
loadDocs();
