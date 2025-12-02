// static/visibility.js
document.addEventListener("DOMContentLoaded", () => {
  // ============================================================
  // 1) Generic "visible_if" support for arbitrary fields
  // ============================================================
  const conditionalFields = document.querySelectorAll("[data-visible-if-field]");

  function getFieldValue(name) {
    const elements = document.querySelectorAll(`[name="${name}"]`);
    if (!elements.length) return "";

    const el = elements[0];

    // <select>
    if (el.tagName === "SELECT") {
      return el.value;
    }

    // radio group
    if (el.type === "radio") {
      const checked = document.querySelector(`input[name="${name}"]:checked`);
      return checked ? checked.value : "";
    }

    // checkbox (single or group): normalize to "true"/"false"
    if (el.type === "checkbox") {
      const checked = document.querySelector(`input[name="${name}"]:checked`);
      return checked ? "true" : "false";
    }

    // default: text/number/etc.
    return el.value || "";
  }

  function updateVisibility() {
    conditionalFields.forEach((el) => {
      const depField = el.dataset.visibleIfField;
      const allowed = (el.dataset.visibleIfValues || "")
        .split(",")
        .map((v) => v.trim())
        .filter((v) => v !== "");
      const current = getFieldValue(depField);

      if (allowed.includes(current)) {
        // special behaviour for nodal-extra so that inputs stay inline
        if (el.classList.contains("nodal-extra")) {
          el.style.display = "inline-flex";
        } else {
          el.style.display = "";
        }
      } else {
        el.style.display = "none";
      }
    });
  }

  // Run once on load
  updateVisibility();

  // Recompute when any controlling field changes
  document.addEventListener("change", (event) => {
    const name = event.target.name;
    if ([...conditionalFields].some((f) => f.dataset.visibleIfField === name)) {
      updateVisibility();
    }
  });

  // ============================================================
  // 2) (Legacy) Histologic type → subtype filtering
  //    For old configs using histologic_type + dependent selects
  // ============================================================
  const histoTypeSelect = document.querySelector('select[name="histologic_type"]');

  function filterHistologicSubtypes() {
    if (!histoTypeSelect) return;

    const currentType = histoTypeSelect.value || "";

    // 2.1 Filter subtype <select> elements
    const subtypeSelects = document.querySelectorAll(
      'select[data-histologic-subtype="true"]'
    );

    subtypeSelects.forEach((select) => {
      const options = select.querySelectorAll("option");
      let firstVisible = null;

      options.forEach((opt) => {
        const parent = opt.dataset.parentType || "";
        const visible = !parent || parent === currentType;

        opt.hidden = !visible;
        opt.disabled = !visible;

        if (visible && !firstVisible) {
          firstVisible = opt;
        }

        // If this option was selected but is now hidden, clear it
        if (!visible && opt.selected) {
          opt.selected = false;
        }
      });

      // If no value is selected and we have a visible candidate, select first
      if (!select.value && firstVisible) {
        firstVisible.selected = true;
      }
    });

    // 2.2 Filter "other subtypes" checkboxes or rows
    const subtypeCheckboxHolders = document.querySelectorAll(
      '[data-histologic-subtype-checkbox="true"]'
    );

    subtypeCheckboxHolders.forEach((holder) => {
      const parent = holder.dataset.parentType || "";
      const checkbox = holder.querySelector('input[type="checkbox"]') || holder;
      const visible = !parent || parent === currentType;

      if (visible) {
        holder.style.display = "";
        if (checkbox instanceof HTMLInputElement) {
          checkbox.disabled = false;
        }
      } else {
        holder.style.display = "none";
        if (checkbox instanceof HTMLInputElement) {
          checkbox.checked = false;
          checkbox.disabled = true;
        }
      }
    });
  }

  if (histoTypeSelect) {
    filterHistologicSubtypes();
    histoTypeSelect.addEventListener("change", filterHistologicSubtypes);
  }

  // ============================================================
  // 3) (Legacy) Subtype percentage visibility toggling
  //    Only affects the "checkbox + % input" pattern
  // ============================================================
  const subtypeRows = document.querySelectorAll(".histologic-subtype-row");

  subtypeRows.forEach((row) => {
    const checkbox = row.querySelector(".histologic-subtype-checkbox");
    const pctInput = row.querySelector(".histologic-subtype-percent");
    if (!checkbox || !pctInput) return;

    function syncPercentVisibility() {
      if (checkbox.checked) {
        pctInput.style.display = "";
        pctInput.disabled = false;
      } else {
        pctInput.style.display = "none";
        pctInput.disabled = true;
        pctInput.value = "";
      }
    }

    syncPercentVisibility();
    checkbox.addEventListener("change", syncPercentVisibility);
  });

  // ============================================================
  // 4) New histologic mix table:
  //    - type → subtype filtering per row
  //    - AD-only percentages
  //    - non-AD: only one row visible
  //    - header / hint hidden when no AD
  // ============================================================
  const AD_CODE = "AD";  // must match YAML type.code for adenocarcinoma
  const mixRows = Array.from(document.querySelectorAll(".histologic-mix-row"));

  // Cache all subtype options per row (except placeholder)
  mixRows.forEach((row) => {
    const subtypeSelect = row.querySelector(".histologic-subtype-select");
    if (subtypeSelect && !row._allSubtypeOptions) {
      row._allSubtypeOptions = Array.from(subtypeSelect.options).slice(1);
    }
  });

  function updateRowSubtypes(row) {
    const typeSelect = row.querySelector(".histologic-type-select");
    const subtypeSelect = row.querySelector(".histologic-subtype-select");
    if (!typeSelect || !subtypeSelect) return;

    const allOptions = row._allSubtypeOptions;
    if (!allOptions) return;

    const currentType = typeSelect.value;
    const currentValue = subtypeSelect.value;

    // Reset to placeholder
    subtypeSelect.innerHTML = "";
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "--";
    subtypeSelect.appendChild(placeholder);

    const candidates = allOptions.filter((opt) => {
      const parent = opt.dataset.parentType || "";
      return !currentType || parent === currentType;
    });

    candidates.forEach((opt) => {
      subtypeSelect.appendChild(opt.cloneNode(true));
    });

    if (
      currentValue &&
      Array.from(subtypeSelect.options).some((o) => o.value === currentValue)
    ) {
      subtypeSelect.value = currentValue;
    }
  }

  function updateRowMode(row) {
    const typeSelect = row.querySelector(".histologic-type-select");
    const pctInput   = row.querySelector(".histologic-percent-input");
    const pctCell    = pctInput ? pctInput.closest("td") : null;
    if (!typeSelect || !pctInput) return;

    const typeCode = typeSelect.value;

    if (typeCode === AD_CODE) {
      // AD: percentage used and required
      pctInput.disabled = false;
      pctInput.required = true;
      pctInput.style.visibility = "visible";
      if (pctCell) pctCell.style.display = "";      // show cell again
    } else if (typeCode === "") {
      // empty type: allow editing but not required
      pctInput.disabled = false;
      pctInput.required = false;
      pctInput.style.visibility = "visible";
      if (pctCell) pctCell.style.display = "";      // keep visible while no type chosen
    } else {
      // non-AD: percentage not used → hide entire cell
      pctInput.value = "";
      pctInput.disabled = true;
      pctInput.required = false;
      pctInput.style.visibility = "hidden";
      if (pctCell) pctCell.style.display = "none";  // hide the td itself
    }
  }

  // function updateRowMode(row) {
  //   const typeSelect = row.querySelector(".histologic-type-select");
  //   const pctInput = row.querySelector(".histologic-percent-input");
  //   if (!typeSelect || !pctInput) return;

  //   const typeCode = typeSelect.value;

  //   if (typeCode === AD_CODE) {
  //     // AD: percentage used and required
  //     pctInput.disabled = false;
  //     pctInput.required = true;
  //     pctInput.style.visibility = "visible";
  //   } else if (typeCode === "") {
  //     // empty type: keep editable but not required
  //     pctInput.disabled = false;
  //     pctInput.required = false;
  //     pctInput.style.visibility = "visible";
  //   } else {
  //     // non-AD: no percentage
  //     pctInput.value = "";
  //     pctInput.disabled = true;
  //     pctInput.required = false;
  //     pctInput.style.visibility = "hidden";
  //   }
  // }

  // Only one non-AD row (the first) is allowed to stay visible.
  function enforceNonADSingleRowRule() {
    let firstNonADRow = null;

    mixRows.forEach((row) => {
      const typeSelect = row.querySelector(".histologic-type-select");
      if (!typeSelect) return;
      const typeCode = typeSelect.value;

      if (typeCode && typeCode !== AD_CODE && !firstNonADRow) {
        firstNonADRow = row;
      }
    });

    if (!firstNonADRow) {
      // No non-AD rows: all rows available for AD mixture
      mixRows.forEach((row) => {
        row.style.display = "";
      });
      return;
    }

    // Only first non-AD row stays; others are cleared + hidden
    mixRows.forEach((row) => {
      const typeSelect = row.querySelector(".histologic-type-select");
      if (!typeSelect) return;

      if (row === firstNonADRow) {
        row.style.display = "";
      } else {
        const subtypeSelect = row.querySelector(".histologic-subtype-select");
        const pctInput = row.querySelector(".histologic-percent-input");

        typeSelect.value = "";
        if (subtypeSelect) subtypeSelect.value = "";
        if (pctInput) pctInput.value = "";
        row.style.display = "none";
      }
    });
  }

  // AD-only histologic total; also controls header + hint visibility
  function updateHistologicTotal() {
    let total = 0;
    let hasAD = false;

    // Only AD rows contribute to total AND to "hasAD"
    mixRows.forEach((row) => {
      const typeSelect = row.querySelector(".histologic-type-select");
      const pctInput   = row.querySelector(".histologic-percent-input");
      if (!typeSelect || !pctInput) return;

      if (typeSelect.value !== AD_CODE) {
        return;  // skip non-AD and empty types
      }

      hasAD = true;

      const v = parseFloat(pctInput.value);
      if (!isNaN(v)) {
        total += v;
      }
    });

    const hint   = document.querySelector(".histologic-hint");
    const header = document.querySelector(".histologic-percent-header");

    // No AD rows at all: hide header + hint and clear text
    if (!hasAD) {
      if (header) header.style.display = "none";
      if (hint) {
        hint.style.display = "none";
        hint.textContent   = "";
        hint.style.color   = "";
      }
      return;
    }

    // AD rows exist → show header + hint
    if (header) header.style.display = "";
    if (!hint) return;

    hint.style.display = "";

    if (total === 0) {
      hint.textContent =
        "合計が 100% になるように入力します（AD のみ）。主たる組織亜型は最大割合から自動判定されます。";
      hint.style.color = "";
    } else if (Math.abs(total - 100) < 0.5) {
      hint.textContent = `現在の合計: 約 ${total.toFixed(1)}%`;
      hint.style.color = "";
    } else {
      hint.textContent = `現在の合計: 約 ${total.toFixed(
        1
      )}%（100% になるように調整してください）`;
      hint.style.color = "red";
    }
  }

  // Initialize histologic mix rows
  mixRows.forEach((row) => {
    const typeSelect = row.querySelector(".histologic-type-select");
    const subtypeSelect = row.querySelector(".histologic-subtype-select");
    const pctInput = row.querySelector(".histologic-percent-input");
    if (!typeSelect || !subtypeSelect || !pctInput) return;

    // initial setup
    updateRowSubtypes(row);
    updateRowMode(row);

    typeSelect.addEventListener("change", () => {
      updateRowSubtypes(row);
      updateRowMode(row);
      enforceNonADSingleRowRule();
      updateHistologicTotal();
    });

    pctInput.addEventListener("input", () => {
      updateHistologicTotal();
    });
  });

  // Initial total check for AD
  updateHistologicTotal();

  // ============================================================
  // 5) Histologic mix → description textarea helper
  // ============================================================
  function buildHistologicSummaryFromDOM() {
    const rows = Array.from(document.querySelectorAll(".histologic-mix-row"));
    const rowData = [];

    rows.forEach((row) => {
      const typeSel = row.querySelector(".histologic-type-select");
      const subtypeSel = row.querySelector(".histologic-subtype-select");
      const pctInput = row.querySelector(".histologic-percent-input");
      if (!typeSel || !subtypeSel || !pctInput) return;

      const typeCode = (typeSel.value || "").trim();
      const subtypeCode = (subtypeSel.value || "").trim();
      const pctStr = (pctInput.value || "").trim();

      // Skip empty rows
      if (!typeCode && !subtypeCode && !pctStr) return;

      const pct = parseFloat(pctStr);
      const pctVal = isNaN(pct) ? 0 : pct;

      const typeLabel =
        (typeSel.options[typeSel.selectedIndex] &&
          typeSel.options[typeSel.selectedIndex].textContent.trim()) ||
        "";
      const subtypeLabel =
        (subtypeSel.options[subtypeSel.selectedIndex] &&
          subtypeSel.options[subtypeSel.selectedIndex].textContent.trim()) ||
        "";

      rowData.push({
        typeCode,
        subtypeCode,
        pct: pctVal,
        typeLabel,
        subtypeLabel,
      });
    });

    if (!rowData.length) return "";

    const adRows = rowData.filter((r) => r.typeCode === AD_CODE && r.pct > 0);
    const nonAdRows = rowData.filter(
      (r) => r.typeCode && r.typeCode !== AD_CODE
    );

    const parts = [];

    // AD mixture with %
    if (adRows.length) {
      let primary = adRows[0];
      adRows.forEach((r) => {
        if (r.pct > primary.pct) {
          primary = r;
        }
      });

      if (primary.typeLabel) {
        parts.push(primary.typeLabel);
      }

      if (primary.subtypeLabel) {
        parts.push(`${primary.subtypeLabel} (主 ${primary.pct.toFixed(0)}%)`);
      } else if (primary.pct > 0) {
        parts.push(`(主 ${primary.pct.toFixed(0)}%)`);
      }

      adRows.forEach((r) => {
        if (r === primary) return;
        if (!r.pct) return;

        const pctText = `${r.pct.toFixed(0)}%`;
        if (r.subtypeLabel) {
          parts.push(`${r.subtypeLabel} ${pctText}`);
        } else {
          parts.push(pctText);
        }
      });
    }

    // Non-AD rows (no percentages, only one non-AD row should be visible)
    nonAdRows.forEach((r) => {
      if (r.typeLabel && r.subtypeLabel) {
        parts.push(`${r.typeLabel} ${r.subtypeLabel}`);
      } else if (r.typeLabel) {
        parts.push(r.typeLabel);
      } else if (r.subtypeLabel) {
        parts.push(r.subtypeLabel);
      }
    });

    return parts.join(", ");
  }

  const descButton = document.getElementById(
    "btn-fill-description-from-histology"
  );
  if (descButton) {
    descButton.addEventListener("click", () => {
      const textarea = document.querySelector("textarea#description");
      if (!textarea) return;

      const summary = buildHistologicSummaryFromDOM();
      if (!summary) return;

      textarea.value = summary;
      textarea.focus();
    });
  }
});
