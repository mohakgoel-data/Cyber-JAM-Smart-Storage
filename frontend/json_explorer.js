// ------- CONFIG -------
const API_BASE = "http://localhost:8000";

// ------- DOM ELEMENTS -------
const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");
const datasetTableBody = document.getElementById("datasetTableBody");

const jsonViewer = document.getElementById("jsonViewer");
const jsonOutput = document.getElementById("jsonOutput");
const copyJsonBtn = document.getElementById("copyJsonBtn");
const downloadJsonBtn = document.getElementById("downloadJsonBtn");

let currentDatasetData = null;
let currentDatasetId = null;

// --------------------------------------------------
// INITIAL LOAD: show all datasets
// --------------------------------------------------
window.addEventListener("DOMContentLoaded", () => {
  loadDatasets();  // no query => GET /json/datasets
});

// --------------------------------------------------
// SEARCH HANDLERS
// --------------------------------------------------
searchBtn.addEventListener("click", () => {
  const q = searchInput.value.trim();
  loadDatasets(q || null);
});

searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") {
    const q = searchInput.value.trim();
    loadDatasets(q || null);
  }
});

// --------------------------------------------------
// LOAD DATASETS LIST (OPTIONAL QUERY)
// --------------------------------------------------
async function loadDatasets(query = null) {
  jsonViewer.style.display = "none";
  jsonOutput.textContent = "";
  currentDatasetData = null;
  currentDatasetId = null;

  datasetTableBody.innerHTML = `
    <tr>
      <td colspan="4" style="padding:1.5rem;text-align:center;color:var(--muted-foreground);">
        Loading datasets...
      </td>
    </tr>
  `;

  try {
    let url = `${API_BASE}/json/datasets`;
    if (query) {
      url += `?query=${encodeURIComponent(query)}`;
    }

    const res = await fetch(url);
    if (!res.ok) {
      throw new Error(`Failed to load datasets: ${res.status}`);
    }

    const datasets = await res.json();
    renderDatasetTable(datasets, query);

  } catch (err) {
    console.error(err);
    datasetTableBody.innerHTML = `
      <tr>
        <td colspan="4" style="padding:1.5rem;text-align:center;color:red;">
          Error loading datasets.
        </td>
      </tr>
    `;
  }
}

// --------------------------------------------------
// RENDER TABLE ROWS
// --------------------------------------------------
function renderDatasetTable(datasets, query) {
  datasetTableBody.innerHTML = "";

  if (!datasets || datasets.length === 0) {
    datasetTableBody.innerHTML = `
      <tr>
        <td colspan="4" style="padding:1.5rem;text-align:center;color:var(--muted-foreground);">
          ${query ? `No datasets found for "${query}".` : "No datasets stored yet."}
        </td>
      </tr>
    `;
    return;
  }

  // Sort by ID just to keep it stable
  datasets.sort((a, b) => a.id - b.id);

  datasets.forEach(ds => {
    const tr = document.createElement("tr");

    const typeLabel = ds.storage_type ? ds.storage_type.toUpperCase() : "-";
    const name =
      ds.sql_table_name ||
      ds.mongo_collection_name ||
      ds.original_name ||
      `dataset_${ds.id}`;

    const created = ds.created_at
      ? new Date(ds.created_at).toLocaleString()
      : "-";

    tr.innerHTML = `
      <td>${ds.id}</td>
      <td>${typeLabel}</td>
      <td>${name}</td>
      <td>
        <button class="file-action-btn" data-id="${ds.id}">
          View JSON
        </button>
      </td>
    `;

    const btn = tr.querySelector("button");
    btn.addEventListener("click", () => viewDataset(ds.id));

    datasetTableBody.appendChild(tr);
  });
}

// --------------------------------------------------
// VIEW A SINGLE DATASET
// --------------------------------------------------
async function viewDataset(id) {
  jsonViewer.style.display = "none";
  jsonOutput.textContent = "";
  currentDatasetData = null;
  currentDatasetId = null;

  try {
    const res = await fetch(`${API_BASE}/json/${id}`);
    if (!res.ok) {
      throw new Error(`Failed to fetch dataset ${id}: ${res.status}`);
    }

    const payload = await res.json();

    // payload = { dataset_id, storage_type, data }
    currentDatasetId = payload.dataset_id;
    currentDatasetData = payload.data;

    jsonOutput.textContent = JSON.stringify(currentDatasetData, null, 2);
    jsonViewer.style.display = "block";

  } catch (err) {
    console.error(err);
    alert("Error fetching dataset JSON.");
  }
}

// --------------------------------------------------
// COPY JSON
// --------------------------------------------------
copyJsonBtn.addEventListener("click", () => {
  if (!currentDatasetData) return;
  const text = JSON.stringify(currentDatasetData, null, 2);
  navigator.clipboard.writeText(text)
    .then(() => alert("JSON copied to clipboard."))
    .catch(err => {
      console.error(err);
      alert("Failed to copy JSON.");
    });
});

// --------------------------------------------------
// DOWNLOAD JSON
// --------------------------------------------------
downloadJsonBtn.addEventListener("click", () => {
  if (!currentDatasetData) return;

  const blob = new Blob(
    [JSON.stringify(currentDatasetData, null, 2)],
    { type: "application/json" }
  );

  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");

  a.href = url;
  a.download = currentDatasetId
    ? `dataset_${currentDatasetId}.json`
    : "dataset.json";

  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
});
