// static/visibility.js
document.addEventListener("DOMContentLoaded", () => {
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
        .map(v => v.trim())
        .filter(v => v !== "");
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

  // run once on load
  updateVisibility();

  // recompute when any controlling field changes
  document.addEventListener("change", (event) => {
    const name = event.target.name;
    if ([...conditionalFields].some(f => f.dataset.visibleIfField === name)) {
      updateVisibility();
    }
  });
});

// document.addEventListener("DOMContentLoaded", () => {
//   const conditionalFields = document.querySelectorAll("[data-visible-if-field]");

//   function getFieldValue(name) {
//     const elements = document.querySelectorAll(`[name="${name}"]`);
//     if (!elements.length) return "";

//     const el = elements[0];

//     // <select>
//     if (el.tagName === "SELECT") {
//       return el.value;
//     }

//     // radio group
//     if (el.type === "radio") {
//       const checked = document.querySelector(`input[name="${name}"]:checked`);
//       return checked ? checked.value : "";
//     }

//     // checkbox (single or group):
//     // interpret checked/unchecked as "true"/"false" for visibility
//     if (el.type === "checkbox") {
//       const checked = document.querySelector(`input[name="${name}"]:checked`);
//       return checked ? "true" : "false";
//     }

//     // default: text/number/etc.
//     return el.value || "";
//   }

//   function updateVisibility() {
//     conditionalFields.forEach((el) => {
//       const depField = el.dataset.visibleIfField;
//       const allowed = (el.dataset.visibleIfValues || "")
//         .split(",")
//         .map(v => v.trim())
//         .filter(v => v !== "");
//       const current = getFieldValue(depField);

//       if (allowed.includes(current)) {
//         // special behaviour for nodal-extra, if we use it
//         if (el.classList.contains("nodal-extra")) {
//           el.style.display = "inline-flex";
//         } else {
//           el.style.display = "";
//         }
//       } else {
//         el.style.display = "none";
//       }
//     });
//   }

//   // run once on load
//   updateVisibility();

//   // recompute when controlling fields change
//   document.addEventListener("change", (event) => {
//     const name = event.target.name;
//     if ([...conditionalFields].some(f => f.dataset.visibleIfField === name)) {
//       updateVisibility();
//     }
//   });
// });
