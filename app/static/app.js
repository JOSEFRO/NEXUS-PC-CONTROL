(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const state = { scanning: false, largeFiles: false, health: false };
  const number = (value, digits = 2) => Number(value || 0).toFixed(digits);
  const gb = (value) => number(value) + " GB";

  function setText(id, value) {
    const node = $(id);
    if (node) node.textContent = String(value ?? "");
  }

  function make(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function showMessage(container, message, className = "muted") {
    if (!container) return;
    container.replaceChildren(make("p", className, message));
  }

  function appendCoverage(container, coverage) {
    if (!container || !coverage) return;
    const details = [];
    if (coverage.files !== undefined) details.push(Number(coverage.files).toLocaleString("es-DO") + " archivos revisados");
    if (coverage.errors !== undefined) details.push(Number(coverage.errors).toLocaleString("es-DO") + " errores");
    if (coverage.excluded_directories !== undefined) details.push(Number(coverage.excluded_directories).toLocaleString("es-DO") + " carpetas excluidas");
    if (coverage.skipped_symlinks !== undefined) details.push(Number(coverage.skipped_symlinks).toLocaleString("es-DO") + " enlaces omitidos");
    const complete = coverage.complete === true;
    const note = make("p", complete ? "muted" : "notice",
      (complete ? "Cobertura del análisis: completa. " : "Cobertura parcial: revisa los elementos omitidos. ") + details.join(" · "));
    container.append(note);
  }

  async function getJSON(url, options) {
    const response = await fetch(url, {
      ...options,
      headers: { Accept: "application/json", ...(options && options.headers || {}) }
    });
    if (!response.ok) {
      let message = "La solicitud no pudo completarse (" + response.status + ").";
      try {
        const body = await response.json();
        if (body.error) message = body.error;
      } catch { /* Keep the generic message. */ }
      throw new Error(message);
    }
    return response.json();
  }

  function renderDrives(drives) {
    const list = $("drives");
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(drives) || drives.length === 0) {
      showMessage(list, "No se encontraron unidades disponibles.");
      setText("diskUsed", "—");
      setText("diskFree", "Sin datos de almacenamiento");
      if ($("diskBar")) $("diskBar").style.width = "0%";
      return;
    }

    const primary = drives.find((drive) => drive.is_system) || drives[0];
    setText("diskUsed", number(primary.used_percent, 1) + "%");
    setText("diskFree", gb(primary.free_gb) + " libres de " + gb(primary.total_gb));
    if ($("diskBar")) $("diskBar").style.width = Math.max(0, Math.min(100, Number(primary.used_percent) || 0)) + "%";

    drives.forEach((drive) => {
      const row = make("article", "drive-row");
      const info = make("div", "drive-info");
      const kind = drive.is_system ? " · Windows" : (drive.drive_type ? " · " + drive.drive_type : "");
      info.append(make("strong", "", (drive.drive || "Unidad") + kind), make("small", "", gb(drive.used_gb) + " usados · " + gb(drive.free_gb) + " libres"));
      const meter = make("div", "drive-meter");
      const fill = make("i");
      fill.style.width = Math.max(0, Math.min(100, Number(drive.used_percent) || 0)) + "%";
      meter.append(fill);
      row.append(info, make("b", "drive-percent", number(drive.used_percent, 1) + "%"), meter);
      list.append(row);
    });
  }

  function renderFolders(folders, coverage) {
    const list = $("folders");
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(folders) || folders.length === 0) {
      showMessage(list, "No se encontraron carpetas accesibles.");
      appendCoverage(list, coverage);
      return;
    }
    folders.forEach((item) => {
      const row = make("article", "folder");
      const details = make("div");
      details.append(make("b", "", item.name), make("small", "", item.path));
      row.append(details, make("strong", "size", gb(item.size_gb)));
      list.append(row);
    });
    appendCoverage(list, coverage);
  }

  function renderLargeFiles(files, coverage) {
    const list = $("largeFiles");
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(files) || files.length === 0) {
      showMessage(list, "No se encontraron archivos con ese tamaño mínimo.");
      appendCoverage(list, coverage);
      return;
    }
    files.forEach((item) => {
      const row = make("article", "folder");
      const details = make("div");
      details.append(make("b", "", item.name), make("small", "", item.path));
      row.append(details, make("strong", "size", gb(item.size_gb)));
      list.append(row);
    });
    appendCoverage(list, coverage);
  }

  function renderCleanup(items) {
    const list = $("cleanItems");
    if (!list) return;
    list.replaceChildren();
    if (!Array.isArray(items) || items.length === 0) {
      showMessage(list, "No hay ubicaciones temporales disponibles para revisar.");
      return;
    }
    items.forEach((item) => {
      const label = make("label", "checkrow");
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = item.id;
      const details = make("span");
      details.append(make("b", "", item.name + " · " + number(item.size_mb, 1) + " MB"));
      details.append(make("small", "", item.description + " " + item.path));
      label.append(checkbox, details);
      list.append(label);
    });
  }

  async function loadOverview() {
    const data = await getJSON("/api/overview");
    renderDrives(data.drives);
  }

  async function loadHealth() {
    if (state.health) return;
    state.health = true;
    try {
      const health = await getJSON("/api/health");
      setText("cpu", number(health.cpu_percent, 1) + "%");
      setText("ram", number(health.ram_percent, 1) + "%");
      setText("ramFree", gb(health.ram_available_gb) + " disponibles de " + gb(health.ram_total_gb));
      setText("healthInfo", health.windows + " · Python " + health.python);
    } catch (error) {
      setText("healthInfo", "No se pudo consultar el estado: " + error.message);
    } finally {
      state.health = false;
    }
  }

  const terminalStates = new Set(["cancelled", "completed", "completed_with_warnings", "failed"]);
  const wait = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

  async function runBackgroundScan(kind, options, panelId, onResult) {
    const panel = $(panelId);
    if (panel) {
      panel.replaceChildren();
      const status = make("p", "job-status", "Preparando análisis…");
      const progress = document.createElement("progress");
      progress.setAttribute("aria-label", "Progreso del análisis; total desconocido");
      const counters = make("small", "job-counters", "Esperando actividad…");
      const cancel = make("button", "job-cancel", "Cancelar análisis");
      cancel.type = "button";
      cancel.disabled = true;
      let cancelRequested = false;
      cancel.addEventListener("click", async () => {
        if (cancelRequested) return;
        cancelRequested = true;
        cancel.disabled = true;
        status.textContent = "Solicitando cancelación…";
        try { await getJSON("/api/storage/scans/" + job.scan_id + "/cancel", { method: "POST" }); }
        catch (error) { status.textContent = "No se pudo solicitar la cancelación: " + error.message; }
      });
      panel.append(status, progress, counters, cancel);

      let job;
      try {
        job = await getJSON("/api/storage/scans", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ kind, ...options })
        });
        cancel.disabled = false;
        while (true) {
          const snapshot = await getJSON("/api/storage/scans/" + job.scan_id);
          status.textContent = snapshot.phase + " · " + snapshot.status;
          counters.textContent =
            Number(snapshot.files_processed || 0).toLocaleString("es-DO") + " archivos · " +
            Number(snapshot.directories_processed || 0).toLocaleString("es-DO") + " carpetas · " +
            (Number(snapshot.bytes_observed || 0) / (1024 ** 3)).toFixed(2) + " GB observados · " +
            Number(snapshot.error_count || 0).toLocaleString("es-DO") + " errores";
          if (terminalStates.has(snapshot.status)) {
            cancel.hidden = true;
            if (snapshot.result && onResult) onResult(snapshot.result);
            if (snapshot.error) throw new Error(snapshot.error);
            if (snapshot.status === "cancelled") status.textContent += " (se muestran resultados parciales)";
            return snapshot;
          }
          await wait(650);
        }
      } catch (error) {
        if (panel) showMessage(panel, "No se pudo completar el análisis: " + error.message, "error-message");
        throw error;
      }
    }
    const job = await getJSON("/api/storage/scans", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind, ...options })
    });
    while (true) {
      const snapshot = await getJSON("/api/storage/scans/" + job.scan_id);
      if (terminalStates.has(snapshot.status)) {
        if (snapshot.result && onResult) onResult(snapshot.result);
        if (snapshot.error) throw new Error(snapshot.error);
        return snapshot;
      }
      await wait(650);
    }
  }

  async function runScan() {
    if (state.scanning) return;
    state.scanning = true;
    showMessage($("folders"), "Iniciando análisis en segundo plano…");
    try {
      const [overview, cleanup] = await Promise.all([
        getJSON("/api/overview"), getJSON("/api/cleanup")
      ]);
      renderDrives(overview.drives);
      renderCleanup(cleanup.items);
      await loadStorageCategories();
      await runBackgroundScan("profile", {}, "profileJob", (scan) => renderFolders(scan.folders, scan.coverage));
      await loadHealth();
    } catch (error) {
      if (!$("profileJob")?.textContent) showMessage($("folders"), "No se pudo completar el análisis: " + error.message, "error-message");
    } finally {
      state.scanning = false;
    }
  }

  async function loadLarge() {
    if (state.largeFiles) return;
    state.largeFiles = true;
    const threshold = Math.max(1, Math.min(1048576, Number.parseInt($("largeThreshold")?.value || "1024", 10) || 1024));
    showMessage($("largeFiles"), "Iniciando búsqueda en segundo plano…");
    try {
      await runBackgroundScan("large_files", { min_size_mb: threshold }, "largeJob",
        (data) => renderLargeFiles(data.files, data.coverage));
    } catch (error) {
      showMessage($("largeFiles"), "No se pudo completar la búsqueda: " + error.message, "error-message");
    } finally {
      state.largeFiles = false;
    }
  }

  async function cleanSelected() {
    const ids = [...document.querySelectorAll("#cleanItems input:checked")].map((input) => input.value);
    if (!ids.length) {
      showMessage($("cleanResult"), "Selecciona al menos una categoría para revisar.");
      return;
    }
    if (!window.confirm("Vas a eliminar archivos de las ubicaciones temporales seleccionadas. Revisa la selección y confirma solo si estás seguro. ¿Continuar?")) return;

    const button = $("cleanButton");
    if (button) button.disabled = true;
    setText("cleanResult", "Procesando la selección…");
    try {
      const result = await getJSON("/api/cleanup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ ids })
      });
      const summary = (result.results || []).map((item) =>
        item.id + ": " + item.status + (item.archivos_eliminados !== undefined ? " · " + item.archivos_eliminados + " archivos" : "")
      ).join(" | ");
      setText("cleanResult", summary || result.message || "Proceso finalizado.");
      await runScan();
    } catch (error) {
      setText("cleanResult", "No se pudo completar: " + error.message);
    } finally {
      if (button) button.disabled = false;
    }
  }


  let activeStorageCategory = null;
  let activeStoragePath = "";
  const selectedStorageFiles = new Set();
  let storageNavigationRequest = 0;

  async function loadStorageCategories() {
    const data = await getJSON("/api/storage/categories");
    const container = $("storageCategories");
    if (!container) return;
    container.replaceChildren();
    data.categories.forEach((category) => {
      const button = make("button", "category-card", category.name);
      button.type = "button";
      button.addEventListener("click", () => openStorageFolder(category.id, ""));
      container.append(button);
    });
  }

  async function openStorageFolder(categoryId, relativePath) {
    const explorer = $("storageExplorer");
    if (!explorer) return;
    if (activeStorageCategory !== categoryId || activeStoragePath !== (relativePath || "")) selectedStorageFiles.clear();
    activeStorageCategory = categoryId;
    activeStoragePath = relativePath || "";
    const requestId = ++storageNavigationRequest;
    explorer.hidden = false;
    showMessage(explorer, "Leyendo contenido de la carpeta…");
    try {
      const data = await getJSON("/api/storage/browse/" + encodeURIComponent(categoryId) +
        "?path=" + encodeURIComponent(activeStoragePath));
      if (requestId !== storageNavigationRequest) return;
      explorer.replaceChildren();
      const heading = make("div", "explorer-heading");
      const title = make("h3", "", data.category.name + (data.relative_path ? " / " + data.relative_path : ""));
      const back = make("button", "", "← Volver");
      back.type = "button";
      back.disabled = !data.parent_path && !data.relative_path;
      back.addEventListener("click", () => openStorageFolder(categoryId, data.parent_path || ""));
      heading.append(title, back);
      explorer.append(heading);
      const rows = make("div", "folder-list");
      const selected = [];
      data.entries.forEach((entry) => {
        const row = make("div", "explorer-row");
        const details = make("div", "explorer-entry");
        const label = entry.is_dir ? "📁 " + entry.name : "📄 " + entry.name;
        details.append(make("b", "", label));
        details.append(make("small", "", entry.is_dir ? "Carpeta" : (Number(entry.size_bytes).toLocaleString("es-DO") + " bytes · " + (entry.size_bytes / 1073741824).toFixed(3) + " GB")));
        if (entry.is_dir) {
          const open = make("button", "", "Abrir");
          open.type = "button";
          open.addEventListener("click", () => openStorageFolder(categoryId, entry.relative_path));
          row.append(details, open);
        } else {
          const check = document.createElement("input");
          check.type = "checkbox";
          check.setAttribute("aria-label", "Seleccionar " + entry.name);
          check.addEventListener("change", () => {
            if (check.checked) selectedStorageFiles.add(entry.relative_path);
            else selectedStorageFiles.delete(entry.relative_path);
            updateDeleteSelection();
          });
          row.append(check, details);
        }
        rows.append(row);
      });
      if (!data.entries.length) showMessage(rows, "Esta carpeta está vacía.");
      explorer.append(rows);
      const controls = make("div", "explorer-controls");
      const count = make("span", "muted", "Seleccionados: 0");
      count.id = "selectedStorageCount";
      const remove = make("button", "danger", "Eliminar seleccionados");
      remove.type = "button";
      remove.disabled = !data.category.deletable;
      remove.title = data.category.deletable ? "Eliminar los archivos seleccionados" : "Categoría protegida: solo lectura";
      remove.addEventListener("click", deleteStorageSelection);
      controls.append(count, remove);
      explorer.append(controls);
      explorer.dataset.deletable = String(data.category.deletable);
      explorer.dataset.category = categoryId;
      updateDeleteSelection();
    } catch (error) {
      if (requestId === storageNavigationRequest) showMessage(explorer, error.message, "error-message");
    }
  }

  function updateDeleteSelection() {
    const count = $("selectedStorageCount");
    if (count) count.textContent = "Seleccionados: " + selectedStorageFiles.size;
    const explorer = $("storageExplorer");
    const remove = explorer && explorer.querySelector(".explorer-controls .danger");
    if (remove) remove.disabled = !selectedStorageFiles.size || explorer.dataset.deletable !== "true";
  }

  async function deleteStorageSelection() {
    if (!selectedStorageFiles.size || !activeStorageCategory) return;
    const paths = [...selectedStorageFiles];
    const confirmed = window.confirm("Se eliminarán " + paths.length +
      " archivo(s) seleccionados. Esta acción no se puede deshacer desde NEXUS. ¿Confirmas?");
    if (!confirmed) return;
    try {
      const result = await getJSON("/api/storage/delete", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category: activeStorageCategory, paths })
      });
      selectedStorageFiles.clear();
      const freed = (Number(result.bytes_freed || 0) / 1073741824).toFixed(3);
      window.alert("Eliminados: " + result.deleted + " · Espacio liberado: " + freed + " GB");
      await openStorageFolder(activeStorageCategory, activeStoragePath);
      await loadOverview();
    } catch (error) {
      window.alert("No se pudo completar la eliminación: " + error.message);
    }
  }

  window.runScan = runScan;
  window.loadLarge = loadLarge;
  window.loadHealth = loadHealth;
  window.cleanSelected = cleanSelected;

  loadOverview().catch((error) => {
    setText("diskFree", "No se pudieron leer las unidades: " + error.message);
  });
  loadHealth();
})();
