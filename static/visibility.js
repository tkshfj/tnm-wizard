document.addEventListener("DOMContentLoaded", () => {
  const conditionalFields = document.querySelectorAll("[data-visible-if-field]");

  function getFieldValue(name) {
    const el = document.querySelector(`[name="${name}"]`);
    if (!el) return "";

    if (el.tagName === "SELECT") {
      return el.value;
    }

    if (el.type === "radio") {
      const checked = document.querySelector(`input[name="${name}"]:checked`);
      return checked ? checked.value : "";
    }

    return el.value || "";
  }

  function updateVisibility() {
    conditionalFields.forEach((fieldDiv) => {
      const depField = fieldDiv.dataset.visibleIfField;
      const allowed = (fieldDiv.dataset.visibleIfValues || "").split(",");
      const current = getFieldValue(depField);

      if (allowed.includes(current)) {
        fieldDiv.style.display = "";
      } else {
        fieldDiv.style.display = "none";
        // もし非表示時に値をクリアしたいならここで input の value を消す
        // fieldDiv.querySelectorAll("input, select, textarea").forEach(el => el.value = "");
      }
    });
  }

  // watch changes on the whole form (simple & generic)
  document.addEventListener("change", (event) => {
    const name = event.target.name;
    // Only recompute if some conditional field depends on this name
    if ([...conditionalFields].some(f => f.dataset.visibleIfField === name)) {
      updateVisibility();
    }
  });

  // initial state
  updateVisibility();
});
