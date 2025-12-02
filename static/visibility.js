// static/visibility.js
document.addEventListener("DOMContentLoaded", () => {
  // ============================================================
  // 1) Generic "visible_if" support for arbitrary fields
  // ============================================================
  const conditionalFields = document.querySelectorAll("[data-visible-if-field]");

  function getFieldValue(name) {
    // There may be multiple elements with this name (radio/checkbox groups)
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

    // checkbox (single or group):
    // interpret checked/unchecked uniformly as "true"/"false"
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
  //    (for any old config that still uses histologic_type + dependent selects)
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

        // If parent_type is empty, treat as always visible
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
    // initial filter on page load
    filterHistologicSubtypes();
    // re-filter whenever histologic type changes
    histoTypeSelect.addEventListener("change", filterHistologicSubtypes);
  }

  // ============================================================
  // 3) (Optional) Subtype percentage visibility toggling
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

    // initial state
    syncPercentVisibility();
    checkbox.addEventListener("change", syncPercentVisibility);
  });

  // ============================================================
  // 4) Histologic mix rows: type -> subtype filtering per row
  // ============================================================
  const mixRows = document.querySelectorAll(".histologic-mix-row");

  mixRows.forEach((row) => {
    const typeSelect = row.querySelector(".histologic-type-select");
    const subtypeSelect = row.querySelector(".histologic-subtype-select");
    if (!typeSelect || !subtypeSelect) return;

    // clone all subtype options (except the first placeholder "--")
    const allOptions = Array.from(subtypeSelect.options).slice(1);

    function updateSubtypes() {
      const currentType = typeSelect.value;
      const currentValue = subtypeSelect.value;

      // Remove all except placeholder
      subtypeSelect.innerHTML = "";
      const placeholder = document.createElement("option");
      placeholder.value = "";
      placeholder.textContent = "--";
      subtypeSelect.appendChild(placeholder);

      // Re-add only matching options
      const candidates = allOptions.filter((opt) => {
        const parent = opt.dataset.parentType || "";
        return !currentType || parent === currentType;
      });

      candidates.forEach((opt) => {
        subtypeSelect.appendChild(opt.cloneNode(true));
      });

      // if previous value is still valid among candidates, keep it
      if (
        currentValue &&
        Array.from(subtypeSelect.options).some((o) => o.value === currentValue)
      ) {
        subtypeSelect.value = currentValue;
      }
    }

    updateSubtypes();
    typeSelect.addEventListener("change", updateSubtypes);
  });

  // ============================================================
  // 5) Optional: warn if total % != 100 for histologic mix
  // ============================================================
  function updateHistologicTotal() {
    const inputs = document.querySelectorAll(".histologic-percent-input");
    let total = 0;
    inputs.forEach((input) => {
      const v = parseFloat(input.value);
      if (!isNaN(v)) total += v;
    });

    const hint = document.querySelector(".histologic-hint");
    if (!hint) return;

    if (total === 0) {
      hint.textContent =
        "合計が 100% になるように入力します。主たる組織亜型は最大割合から自動判定されます。";
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

  document.addEventListener("input", (ev) => {
    if (
      ev.target.classList &&
      ev.target.classList.contains("histologic-percent-input")
    ) {
      updateHistologicTotal();
    }
  });

  updateHistologicTotal();

  // ============================================================
  // 6) Histologic mix → description textarea helper
  //    Build summary from DOM and write into textarea#description
  // ============================================================
  function buildHistologicSummaryFromDOM() {
    const rows = Array.from(document.querySelectorAll(".histologic-mix-row"));
    const rowData = [];

    rows.forEach((row) => {
      const typeSel = row.querySelector(".histologic-type-select");
      const subtypeSel = row.querySelector(".histologic-subtype-select");
      const pctInput = row.querySelector(".histologic-percent-input");

      if (!typeSel || !subtypeSel || !pctInput) return;

      const pctStr = (pctInput.value || "").trim();
      const typeCode = (typeSel.value || "").trim();
      const subtypeCode = (subtypeSel.value || "").trim();

      // skip completely empty rows
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

    // primary = row with largest percentage
    let primary = rowData[0];
    rowData.forEach((r) => {
      if (r.pct > primary.pct) {
        primary = r;
      }
    });

    const parts = [];

    // Primary: base type label
    if (primary.typeLabel) {
      parts.push(primary.typeLabel);
    }

    // Primary subtype with "(主 xx%)"
    if (primary.subtypeLabel) {
      parts.push(`${primary.subtypeLabel} (主 ${primary.pct.toFixed(0)}%)`);
    } else if (primary.pct > 0) {
      parts.push(`(主 ${primary.pct.toFixed(0)}%)`);
    }

    // Other rows
    rowData.forEach((r) => {
      if (r === primary || !r.pct) return;

      const tLabel = r.typeLabel;
      const sLabel = r.subtypeLabel;
      const pctText = `${r.pct.toFixed(0)}%`;

      // Same type as primary -> don't repeat type label
      if (r.typeCode === primary.typeCode && primary.typeLabel) {
        if (sLabel) {
          parts.push(`${sLabel} ${pctText}`);
        } else {
          parts.push(pctText);
        }
      } else {
        // Different histologic type: show both if available
        if (tLabel && sLabel) {
          parts.push(`${tLabel} ${sLabel} ${pctText}`);
        } else if (tLabel) {
          parts.push(`${tLabel} ${pctText}`);
        } else if (sLabel) {
          parts.push(`${sLabel} ${pctText}`);
        }
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

      // overwrite; or change to append if we want to keep existing text
      textarea.value = summary;
      textarea.focus();
    });
  }
});
