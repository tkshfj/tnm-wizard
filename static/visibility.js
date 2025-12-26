// static-src/visibility.ts
import { qsT, qsaT, byIdT } from "./dom.js";
const AD_CODE = "AD"; // must match YAML type.code for adenocarcinoma
// ------------------------------
// Small UI helpers
// ------------------------------
function setDisplay(el, display) {
    if (el instanceof HTMLElement)
        el.style.display = display;
}
function setVisibility(el, visible, displayMode = "") {
    if (!(el instanceof HTMLElement))
        return;
    el.style.display = visible ? displayMode : "none";
}
// ------------------------------
// 1) Generic "visible_if" support
// ------------------------------
function getNamedElements(name) {
    return qsaT(`[name="${CSS.escape(name)}"]`);
}
function getCheckedInputValue(name) {
    return qsT(`input[name="${CSS.escape(name)}"]:checked`)?.value ?? "";
}
function getCheckboxBoolValue(name) {
    return qsT(`input[name="${CSS.escape(name)}"]:checked`) ? "true" : "false";
}
function getInputValue(el, name) {
    switch (el.type) {
        case "radio":
            return getCheckedInputValue(name);
        case "checkbox":
            return getCheckboxBoolValue(name);
        default:
            return el.value ?? "";
    }
}
function getFieldValue(name) {
    const elements = getNamedElements(name);
    if (!elements.length)
        return "";
    const el = elements[0];
    if (el instanceof HTMLSelectElement)
        return el.value ?? "";
    if (el instanceof HTMLInputElement)
        return getInputValue(el, name);
    return el.value ?? "";
}
function updateVisibility(conditionalFields) {
    for (const el of conditionalFields) {
        const depField = el.dataset.visibleIfField ?? "";
        const allowed = (el.dataset.visibleIfValues ?? "")
            .split(",")
            .map((v) => v.trim())
            .filter(Boolean);
        const current = depField ? getFieldValue(depField) : "";
        const ok = allowed.includes(current);
        const displayMode = el.classList.contains("nodal-extra") ? "inline-flex" : "";
        setVisibility(el, ok, displayMode);
    }
}
// ------------------------------
// 2) (Legacy) type -> subtype filtering (old config)
// ------------------------------
function filterSubtypeSelectOptions(currentType) {
    const subtypeSelects = qsaT('select[data-histologic-subtype="true"]');
    for (const select of subtypeSelects) {
        const options = qsaT("option", select);
        let firstVisible = null;
        for (const opt of options) {
            const parent = opt.dataset.parentType ?? "";
            const visible = !parent || parent === currentType;
            opt.hidden = !visible;
            opt.disabled = !visible;
            if (visible && !firstVisible)
                firstVisible = opt;
            if (!visible && opt.selected)
                opt.selected = false;
        }
        if (!select.value && firstVisible)
            firstVisible.selected = true;
    }
}
function filterSubtypeCheckboxRows(currentType) {
    const holders = qsaT('[data-histologic-subtype-checkbox="true"]');
    for (const holder of holders) {
        const parent = holder.dataset.parentType ?? "";
        const visible = !parent || parent === currentType;
        const checkbox = qsT('input[type="checkbox"]', holder);
        setVisibility(holder, visible);
        if (!checkbox)
            continue;
        checkbox.disabled = !visible;
        if (!visible)
            checkbox.checked = false;
    }
}
function filterHistologicSubtypes(histoTypeSelect) {
    if (!histoTypeSelect)
        return;
    const currentType = histoTypeSelect.value ?? "";
    filterSubtypeSelectOptions(currentType);
    filterSubtypeCheckboxRows(currentType);
}
// ------------------------------
// 3) (Legacy) checkbox + % input pattern
// ------------------------------
function wireLegacySubtypePercentRows() {
    const subtypeRows = qsaT(".histologic-subtype-row");
    for (const row of subtypeRows) {
        const checkbox = qsT(".histologic-subtype-checkbox", row);
        const pctInput = qsT(".histologic-subtype-percent", row);
        if (!checkbox || !pctInput)
            continue;
        const sync = () => {
            const on = checkbox.checked;
            setDisplay(pctInput, on ? "" : "none");
            pctInput.disabled = !on;
            if (!on)
                pctInput.value = "";
        };
        sync();
        checkbox.addEventListener("change", sync);
    }
}
function getMixRows() {
    const rows = qsaT(".histologic-mix-row");
    const out = [];
    for (const row of rows) {
        const typeSelect = qsT(".histologic-type-select", row);
        const subtypeSelect = qsT(".histologic-subtype-select", row);
        const pctInput = qsT(".histologic-percent-input", row);
        if (!typeSelect || !subtypeSelect || !pctInput)
            continue;
        out.push({ row, typeSelect, subtypeSelect, pctInput });
    }
    return out;
}
const subtypeOptionsCache = new WeakMap();
function cacheSubtypeOptions(mixRows) {
    for (const r of mixRows) {
        if (subtypeOptionsCache.has(r.row))
            continue;
        subtypeOptionsCache.set(r.row, Array.from(r.subtypeSelect.options).slice(1));
    }
}
function rebuildSubtypeOptions(r) {
    const allOptions = subtypeOptionsCache.get(r.row);
    if (!allOptions)
        return;
    const currentType = r.typeSelect.value;
    const currentValue = r.subtypeSelect.value;
    r.subtypeSelect.innerHTML = "";
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "--";
    r.subtypeSelect.appendChild(placeholder);
    for (const opt of allOptions) {
        const parent = opt.dataset.parentType ?? "";
        const visible = !currentType || parent === currentType;
        if (!visible)
            continue;
        r.subtypeSelect.appendChild(opt.cloneNode(true));
    }
    if (currentValue && Array.from(r.subtypeSelect.options).some((o) => o.value === currentValue)) {
        r.subtypeSelect.value = currentValue;
    }
}
function applyPctMode(r) {
    const typeCode = r.typeSelect.value;
    const pctCell = r.pctInput.closest("td");
    const isAD = typeCode === AD_CODE;
    const isEmpty = typeCode === "";
    const show = isAD || isEmpty;
    // % input rules
    r.pctInput.disabled = !show;
    r.pctInput.required = isAD;
    if (!show)
        r.pctInput.value = "";
    // visibility vs display:
    // - for non-AD we hide the whole cell
    // - for AD/empty we show the cell and the input
    r.pctInput.style.visibility = show ? "visible" : "hidden";
    setDisplay(pctCell, show ? "" : "none");
}
function enforceNonADSingleRowRule(mixRows) {
    let firstNonAD = null;
    for (const r of mixRows) {
        const code = r.typeSelect.value;
        if (code && code !== AD_CODE && !firstNonAD)
            firstNonAD = r;
    }
    if (!firstNonAD) {
        for (const r of mixRows)
            setDisplay(r.row, "");
        return;
    }
    for (const r of mixRows) {
        const keep = r === firstNonAD;
        setDisplay(r.row, keep ? "" : "none");
        if (!keep) {
            r.typeSelect.value = "";
            r.subtypeSelect.value = "";
            r.pctInput.value = "";
        }
    }
}
function calcADTotal(mixRows) {
    let total = 0;
    let hasAD = false;
    for (const r of mixRows) {
        if (r.typeSelect.value !== AD_CODE)
            continue;
        hasAD = true;
        const v = Number.parseFloat(r.pctInput.value);
        if (!Number.isNaN(v))
            total += v;
    }
    return { total, hasAD };
}
function updateHistologicTotal(mixRows) {
    const { total, hasAD } = calcADTotal(mixRows);
    const hint = qsT(".histologic-hint");
    const header = qsT(".histologic-percent-header");
    setDisplay(header, hasAD ? "" : "none");
    if (!hint)
        return;
    if (!hasAD) {
        hint.style.display = "none";
        hint.textContent = "";
        hint.style.color = "";
        return;
    }
    hint.style.display = "";
    hint.style.color = "";
    if (total === 0) {
        hint.textContent =
            "合計が 100% になるように入力します（AD のみ）。主たる組織亜型は最大割合から自動判定されます。";
        return;
    }
    if (Math.abs(total - 100) < 0.5) {
        hint.textContent = `現在の合計: 約 ${total.toFixed(1)}%`;
        return;
    }
    hint.textContent = `現在の合計: 約 ${total.toFixed(1)}%（100% になるように調整してください）`;
    hint.style.color = "red";
}
function initMixTable() {
    const mixRows = getMixRows();
    cacheSubtypeOptions(mixRows);
    const onTypeChange = (r) => {
        rebuildSubtypeOptions(r);
        applyPctMode(r);
        enforceNonADSingleRowRule(mixRows);
        updateHistologicTotal(mixRows);
    };
    for (const r of mixRows) {
        rebuildSubtypeOptions(r);
        applyPctMode(r);
        r.typeSelect.addEventListener("change", () => onTypeChange(r));
        r.pctInput.addEventListener("input", () => updateHistologicTotal(mixRows));
    }
    updateHistologicTotal(mixRows);
    return mixRows;
}
function collectMixRowData(mixRows) {
    const out = [];
    for (const r of mixRows) {
        const typeCode = (r.typeSelect.value ?? "").trim();
        const subtypeCode = (r.subtypeSelect.value ?? "").trim();
        const pctStr = (r.pctInput.value ?? "").trim();
        if (!typeCode && !subtypeCode && !pctStr)
            continue;
        const pctNum = Number.parseFloat(pctStr);
        const pct = Number.isNaN(pctNum) ? 0 : pctNum;
        out.push({
            typeCode,
            subtypeCode,
            pct,
            typeLabel: r.typeSelect.selectedOptions[0]?.textContent?.trim() ?? "",
            subtypeLabel: r.subtypeSelect.selectedOptions[0]?.textContent?.trim() ?? "",
        });
    }
    return out;
}
function findPrimaryAD(adRows) {
    return adRows.reduce((best, cur) => (cur.pct > best.pct ? cur : best), adRows[0]);
}
function formatADMixture(adRows) {
    if (!adRows.length)
        return [];
    const primary = findPrimaryAD(adRows);
    const parts = [];
    if (primary.typeLabel)
        parts.push(primary.typeLabel);
    if (primary.subtypeLabel) {
        parts.push(`${primary.subtypeLabel} (主 ${primary.pct.toFixed(0)}%)`);
    }
    else if (primary.pct > 0) {
        parts.push(`(主 ${primary.pct.toFixed(0)}%)`);
    }
    for (const r of adRows) {
        if (r === primary)
            continue;
        if (!r.pct)
            continue;
        const pctText = `${r.pct.toFixed(0)}%`;
        parts.push(r.subtypeLabel ? `${r.subtypeLabel} ${pctText}` : pctText);
    }
    return parts;
}
function formatNonADRows(nonAdRows) {
    const parts = [];
    for (const r of nonAdRows) {
        if (r.typeLabel && r.subtypeLabel)
            parts.push(`${r.typeLabel} ${r.subtypeLabel}`);
        else if (r.typeLabel)
            parts.push(r.typeLabel);
        else if (r.subtypeLabel)
            parts.push(r.subtypeLabel);
    }
    return parts;
}
function buildHistologicSummaryFromDOM(mixRows) {
    const rowData = collectMixRowData(mixRows);
    if (!rowData.length)
        return "";
    const adRows = rowData.filter((x) => x.typeCode === AD_CODE && x.pct > 0);
    const nonAdRows = rowData.filter((x) => x.typeCode && x.typeCode !== AD_CODE);
    return [...formatADMixture(adRows), ...formatNonADRows(nonAdRows)].join(", ");
}
// ------------------------------
// Boot
// ------------------------------
document.addEventListener("DOMContentLoaded", () => {
    // 1) visible_if
    const conditionalFields = qsaT("[data-visible-if-field]");
    updateVisibility(conditionalFields);
    document.addEventListener("change", (event) => {
        const target = event.target;
        if (!(target instanceof HTMLElement))
            return;
        const name = target instanceof HTMLInputElement || target instanceof HTMLSelectElement ? target.name : "";
        if (!name)
            return;
        if (conditionalFields.some((f) => f.dataset.visibleIfField === name)) {
            updateVisibility(conditionalFields);
        }
    });
    // 2) legacy histologic type -> subtype
    const histoTypeSelect = qsT('select[name="histologic_type"]');
    if (histoTypeSelect) {
        filterHistologicSubtypes(histoTypeSelect);
        histoTypeSelect.addEventListener("change", () => filterHistologicSubtypes(histoTypeSelect));
    }
    // 3) legacy subtype % toggle
    wireLegacySubtypePercentRows();
    // 4) new mix table
    const mixRows = initMixTable();
    // 5) fill description button
    const descButton = byIdT("btn-fill-description-from-histology");
    if (descButton) {
        descButton.addEventListener("click", () => {
            const textarea = qsT("textarea#description");
            if (!textarea)
                return;
            const summary = buildHistologicSummaryFromDOM(mixRows);
            if (!summary)
                return;
            textarea.value = summary;
            textarea.focus();
        });
    }
});
export const __visibility_ts_module = true;
