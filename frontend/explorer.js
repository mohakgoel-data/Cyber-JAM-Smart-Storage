const folderTreeEl = document.getElementById("folderTree");
const fileTableBody = document.getElementById("fileTableBody");
const refreshBtn = document.getElementById("refreshBtn");

const searchInput = document.getElementById("searchInput");
const searchBtn = document.getElementById("searchBtn");

let currentFolderKey = null;   // e.g. "documents/pdf" or "json_data"

/**
 * Fetch the tree from backend
 */
async function loadTree() {
  try {
    const res = await fetch("http://localhost:8000/files/tree");
    const tree = await res.json();
    renderFolderTree(tree);
  } catch (err) {
    console.error(err);
    setTableMessage("Error loading files.");
  }
}

/**
 * Build folder tree UI.
 * tree = { category: { subfolder: [files] } or [files] }
 */
function renderFolderTree(tree) {
  folderTreeEl.innerHTML = "";

  const categories = Object.keys(tree);
  if (categories.length === 0) {
    folderTreeEl.textContent = "No files stored yet.";
    return;
  }

  categories.forEach(category => {
    const value = tree[category];

    const groupDiv = document.createElement("div");
    groupDiv.className = "folder-item";

    // Category button
    const catBtn = document.createElement("button");
    catBtn.className = "folder-button";
    catBtn.innerHTML = `<span class="folder-icon">📁</span><span>${category}</span>`;
    catBtn.addEventListener("click", () => {
      // If category directly has files (no subfolders)
      if (Array.isArray(value)) {
        currentFolderKey = category;
        highlightActiveFolder(groupDiv);
        renderFiles(value);
      }
    });

    groupDiv.appendChild(catBtn);

    // Subfolders
    if (!Array.isArray(value)) {
      const subList = document.createElement("div");
      subList.className = "subfolder-list";

      Object.keys(value).forEach(sub => {
        const subFiles = value[sub];
        if (!subFiles || subFiles.length === 0) return; // skip empty

        const subItem = document.createElement("div");
        subItem.className = "folder-item";

        const subBtn = document.createElement("button");
        subBtn.className = "folder-button";
        subBtn.innerHTML = `<span class="folder-icon">📂</span><span>${category}/${sub}</span>`;

        subBtn.addEventListener("click", () => {
          currentFolderKey = `${category}/${sub}`;
          highlightActiveFolder(subItem);
          renderFiles(subFiles);
        });

        subItem.appendChild(subBtn);
        subList.appendChild(subItem);
      });

      groupDiv.appendChild(subList);
    }

    folderTreeEl.appendChild(groupDiv);
  });
}

/**
 * Highlight selected folder
 */
function highlightActiveFolder(activeElement) {
  const all = folderTreeEl.querySelectorAll(".folder-item");
  all.forEach(el => {
    const btn = el.querySelector(".folder-button");
    if (btn) btn.classList.remove("active");
  });

  const btn = activeElement.querySelector(".folder-button");
  if (btn) btn.classList.add("active");
}

/**
 * Render files in table
 */
function renderFiles(files) {
  if (!files || files.length === 0) {
    setTableMessage("No files in this folder.");
    return;
  }

  fileTableBody.innerHTML = "";
  files.forEach(file => {
    const tr = document.createElement("tr");

    // Type: from mime or extension
    const type = deriveType(file);

    // Size
    const size = formatSize(file.size_bytes);

    // Created
    const created = file.created_at ? formatDate(file.created_at) : "-";

    tr.innerHTML = `
      <td>
        <div class="file-name-cell">
          <span class="file-icon">${iconForType(type)}</span>
          <span>${file.name}</span>
        </div>
      </td>
      <td>${type}</td>
      <td>${size}</td>
      <td>${created}</td>
      <td>
        <div class="file-actions">
          <button class="file-action-btn" data-action="view" data-id="${file.id}">View</button>
          <button class="file-action-btn" data-action="download" data-id="${file.id}">Download</button>
          <button class="file-action-btn" data-action="delete" data-id="${file.id}">Delete</button>
        </div>
      </td>
    `;

    fileTableBody.appendChild(tr);
  });

  // Attach action handlers
  fileTableBody.querySelectorAll(".file-action-btn").forEach(btn => {
    btn.addEventListener("click", handleFileAction);
  });
}

function setTableMessage(msg) {
  fileTableBody.innerHTML = `
    <tr>
      <td colspan="5" style="text-align:center; color: var(--muted-foreground); padding: 1.5rem;">
        ${msg}
      </td>
    </tr>
  `;
}

function deriveType(file) {
  if (file.mime_type) {
    if (file.mime_type.startsWith("image/")) return "image";
    if (file.mime_type === "application/pdf") return "pdf";
    if (file.mime_type.startsWith("video/")) return "video";
    if (file.mime_type.startsWith("audio/")) return "audio";
  }
  // fallback from path
  if (file.stored_path) {
    const parts = file.stored_path.split(".");
    if (parts.length > 1) {
      return parts[parts.length - 1].toLowerCase();
    }
  }
  return "file";
}

function iconForType(type) {
  if (type === "image") return "🖼️";
  if (type === "pdf") return "📄";
  if (type === "video") return "🎥";
  if (type === "audio") return "🎧";
  if (["doc", "docx","text"].includes(type)) return "📘";
  if (["xls", "xlsx", "csv"].includes(type)) return "📊";
  if (["py", "js", "java"].includes(type)) return "💻";
  return "📁";
}

function formatSize(bytes) {
  if (!bytes || bytes <= 0) return "-";
  if (bytes < 1024) return `${bytes} B`;
  const kb = bytes / 1024;
  if (kb < 1024) return `${kb.toFixed(1)} KB`;
  const mb = kb / 1024;
  return `${mb.toFixed(1)} MB`;
}

function formatDate(isoStr) {
  try {
    const d = new Date(isoStr);
    return d.toLocaleString();
  } catch {
    return isoStr;
  }
}

/**
 * Handle View / Download / Delete
 */
async function handleFileAction(e) {
  const btn = e.currentTarget;
  const id = btn.getAttribute("data-id");
  const action = btn.getAttribute("data-action");

  if (action === "view") {
    const res = await fetch(`http://localhost:8000/view/${id}`);
    const data = await res.json();
    window.open(data.url, "_blank");
  }

  if (action === "download") {
    const res = await fetch(`http://localhost:8000/download/${id}`);
    const data = await res.json();
    window.location.href = data.url;
  }

  if (action === "delete") {
    const confirmDelete = window.confirm("Are you sure you want to delete this file?");
    if (!confirmDelete) return;

    const res = await fetch(`http://localhost:8000/delete/${id}`, {
      method: "DELETE"
    });

    if (res.ok) {
      await loadTree();
      setTableMessage("File deleted. Select a folder again.");
    } else {
      console.error("Delete failed", await res.text());
      alert("Failed to delete file.");
    }
  }
}

// -------------------------
// SEARCH FUNCTIONALITY
// -------------------------

searchBtn.addEventListener("click", handleSearch);
searchInput.addEventListener("keypress", (e) => {
  if (e.key === "Enter") handleSearch();
});

async function handleSearch() {
  const query = searchInput.value.trim();
  if (!query) return;

  try {
    const res = await fetch(`http://localhost:8000/search?query=${encodeURIComponent(query)}`);
    if (!res.ok) throw new Error("Search failed");

    const results = await res.json();
    fileTableBody.innerHTML = "";

    if (results.length === 0) {
      setTableMessage(`No files found for "${query}"`);
      return;
    }

    results.forEach(file => {
      const tr = document.createElement("tr");

      const type = deriveType(file);
      const size = formatSize(file.size_bytes);
      const created = file.created_at ? formatDate(file.created_at) : "-";

      tr.innerHTML = `
        <td>
          <div class="file-name-cell">
            <span class="file-icon">${iconForType(type)}</span>
            <span>${file.name || file.original_name}</span>
          </div>
        </td>
        <td>${type}</td>
        <td>${size}</td>
        <td>${created}</td>
        <td>
          <div class="file-actions">
            <button class="file-action-btn" data-action="view" data-id="${file.id}">View</button>
            <button class="file-action-btn" data-action="download" data-id="${file.id}">Download</button>
            <button class="file-action-btn" data-action="delete" data-id="${file.id}">Delete</button>
          </div>
        </td>
      `;

      fileTableBody.appendChild(tr);
    });

    fileTableBody.querySelectorAll(".file-action-btn").forEach(btn => {
      btn.addEventListener("click", handleFileAction);
    });

  } catch (err) {
    console.error(err);
    alert("Search failed. Check backend.");
  }
}


// Refresh button
refreshBtn.addEventListener("click", () => {
  loadTree();
  setTableMessage("Select a folder on the left to view files.");
});

// Init
loadTree();
