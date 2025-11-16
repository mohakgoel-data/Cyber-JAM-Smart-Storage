let selectedFile = null;
let isUploading = false;

// ---------- DOM ELEMENTS ----------
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const browseBtn = document.getElementById('browseBtn');
const uploadBtn = document.getElementById('uploadBtn');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const resultsContainer = document.getElementById('resultsContainer');
const uploadedFileName = document.getElementById('uploadedFileName');
const viewFileLink = document.getElementById('viewFileLink');
const uploadBtnIcon = document.getElementById('uploadBtnIcon');
const uploadBtnText = document.getElementById('uploadBtnText');

const detailsToggle = document.getElementById('detailsToggle');
const detailsContent = document.getElementById('detailsContent');
const metaStoredAs = document.getElementById('metaStoredAs');
const metaCategory = document.getElementById('metaCategory');
const metaFileId = document.getElementById('metaFileId');

// JSON UI
const showJsonBtn = document.getElementById("showJsonBtn");
const jsonUploadSection = document.getElementById("jsonUploadSection");
const backToFileBtn = document.getElementById("backToFileBtn");

const jsonTextarea = document.getElementById("jsonTextarea");
const jsonFileInput = document.getElementById("jsonFileInput");
const browseJsonBtn = document.getElementById("browseJsonBtn");
const uploadJsonBtn = document.getElementById("uploadJsonBtn");

const jsonResult = document.getElementById("jsonResult");
const jsonResultContent = document.getElementById("jsonResultContent");


// --------------------------------------------------------------
// FILE UPLOAD SECTION
// --------------------------------------------------------------
dropZone.addEventListener('dragenter', e => {
  e.preventDefault();
  dropZone.classList.add('dragging');
});

dropZone.addEventListener('dragleave', e => {
  e.preventDefault();
  dropZone.classList.remove('dragging');
});

dropZone.addEventListener('dragover', e => e.preventDefault());

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('dragging');
  if (e.dataTransfer.files.length > 0) {
    handleFileSelection(e.dataTransfer.files[0]);
  }
});

fileInput.addEventListener('change', e => {
  if (e.target.files.length > 0) {
    handleFileSelection(e.target.files[0]);
  }
});

browseBtn.addEventListener('click', () => fileInput.click());

function handleFileSelection(file) {
  selectedFile = file;
  fileNameDisplay.textContent = file.name;
  uploadBtn.disabled = false;
  resultsContainer.style.display = 'none';
}

detailsToggle.addEventListener('click', () => {
  const open = detailsContent.classList.toggle('open');
  detailsToggle.textContent = open ? "Details ▲" : "Details ▼";
});

uploadBtn.addEventListener('click', handleUpload);

// -------------------- FILE UPLOAD HANDLER --------------------
async function handleUpload() {
  if (!selectedFile || isUploading) return;

  isUploading = true;
  uploadBtn.disabled = true;

  uploadBtnIcon.innerHTML = `
    <svg class="btn-icon spinner" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
      <path d="M21 12a9 9 0 1 1-6.219-8.56"/>
    </svg>`;
  uploadBtnText.textContent = "Uploading...";

  const form = new FormData();
  form.append("file", selectedFile);

  try {
    const res = await fetch("http://localhost:8000/upload", { method: "POST", body: form });

    if (!res.ok) throw new Error("Upload failed");

    const data = await res.json();

    uploadedFileName.textContent = data.stored_as;

    const viewRes = await fetch(`http://localhost:8000/view/${data.id}`);
    const viewData = await viewRes.json();

    viewFileLink.href = viewData.url;
    resultsContainer.style.display = "block";

    metaStoredAs.textContent = data.stored_as;
    metaCategory.textContent = data.stored_as.split("/")[0];
    metaFileId.textContent = data.id;

    detailsContent.classList.remove("open");
    detailsToggle.textContent = "Details ▼";

    showToast("Upload successful", `${selectedFile.name} has been uploaded.`);
  } catch (err) {
    console.error(err);
    showToast("Upload failed", "Error uploading file.");
  } finally {
    uploadBtnIcon.innerHTML = `
      <svg class="btn-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
        <polyline points="17 8 12 3 7 8"/>
        <line x1="12" x2="12" y1="3" y2="15"/>
      </svg>`;
    uploadBtnText.textContent = "Upload";

    isUploading = false;
    uploadBtn.disabled = false;
  }
}


// --------------------------------------------------------------
// JSON UPLOAD SECTION
// --------------------------------------------------------------
showJsonBtn.addEventListener("click", () => {
  document.querySelector(".upload-container").style.display = "none";
  resultsContainer.style.display = "none";

  jsonUploadSection.style.display = "block";
});

backToFileBtn.addEventListener("click", () => {
  jsonUploadSection.style.display = "none";
  jsonResult.style.display = "none";

  document.querySelector(".upload-container").style.display = "block";
});

browseJsonBtn.addEventListener("click", () => jsonFileInput.click());

jsonFileInput.addEventListener("change", () => {
  if (jsonFileInput.files.length > 0) {
    const file = jsonFileInput.files[0];
    const reader = new FileReader();

    reader.onload = () => {
      jsonTextarea.value = reader.result;
    };
    reader.readAsText(file);
  }
});

// -------------------- JSON UPLOAD HANDLER --------------------
uploadJsonBtn.addEventListener("click", async () => {
  const raw = jsonTextarea.value.trim();

  if (!raw) {
    showToast("Error", "No JSON provided.");
    return;
  }

  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (e) {
    showToast("Invalid JSON", "Please fix JSON syntax errors.");
    return;
  }

  try {
    const res = await fetch("http://localhost:8000/json/upload", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: raw
    });

    const data = await res.json();

    jsonResult.style.display = "block";
    jsonResultContent.textContent = JSON.stringify(data, null, 2);

    showToast("JSON Stored", "JSON successfully processed.");
  } catch (err) {
    console.error(err);
    showToast("Upload failed", "Could not send JSON.");
  }
});


// --------------------------------------------------------------
// Toast Notifications
// --------------------------------------------------------------
function showToast(title, description) {
  const toast = document.createElement('div');
  toast.style.cssText = `
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    background: var(--card);
    padding: 1rem 1.5rem;
    border-radius: .75rem;
    border: 1px solid var(--border);
    box-shadow: var(--shadow-xl);
    animation: slideIn .3s ease-out;
    z-index: 9999;
  `;
  toast.innerHTML = `
    <div style="font-weight:600">${title}</div>
    <div style="font-size:.875rem; color:var(--muted-foreground)">${description}</div>
  `;
  document.body.appendChild(toast);

  setTimeout(() => {
    toast.style.animation = "slideOut .3s ease-in";
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}

const style = document.createElement("style");
style.textContent = `
@keyframes slideIn { from{transform:translateX(100%);opacity:0;} to{transform:translateX(0);opacity:1;} }
@keyframes slideOut { from{transform:translateX(0);opacity:1;} to{transform:translateX(100%);opacity:0;} }
`;
document.head.appendChild(style);
