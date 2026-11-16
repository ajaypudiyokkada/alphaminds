(function () {
  const TYPE_TO_FIELD = {
    integer: "numeric_value",
    decimal: "numeric_value",
    text: "text_value",
    boolean: "boolean_value",
    date: "date_value",
    json: "json_value",
  };

  const ALL_TYPED_FIELDS = [
    "numeric_value",
    "text_value",
    "boolean_value",
    "date_value",
    "json_value",
  ];

  function rowFieldCell(row, fieldName) {
    return row.querySelector(".field-" + fieldName);
  }

  function rowFieldInput(row, fieldName) {
    return row.querySelector(
      `[name$="-${fieldName}"], textarea[name$="-${fieldName}"], select[name$="-${fieldName}"]`
    );
  }

  function rowMetricDefinitionSelect(row) {
    return row.querySelector('select[name$="-metric_definition"]');
  }

  function rowValueTypeInput(row) {
    return row.querySelector('select[name$="-value_data_type"], input[name$="-value_data_type"]');
  }

  function rowUnitsInput(row) {
    return row.querySelector('input[name$="-units"]');
  }

  function enableCell(cell, enabled) {
    if (!cell) return;
    cell.style.display = enabled ? "" : "none";

    cell.querySelectorAll("input, select, textarea").forEach(function (el) {
      el.disabled = !enabled;
    });
  }

  function clearIrrelevantInputs(row, keepField) {
    ALL_TYPED_FIELDS.forEach(function (fieldName) {
      if (fieldName === keepField) return;

      const input = rowFieldInput(row, fieldName);
      if (!input) return;

      if (input.type === "checkbox") {
        input.checked = false;
      } else if (input.tagName === "SELECT") {
        input.selectedIndex = 0;
      } else {
        input.value = "";
      }
    });
  }

  function updateRow(row) {
    const typeInput = rowValueTypeInput(row);
    if (!typeInput) return;

    const rawType = (typeInput.value || "").toLowerCase().trim();
    const keepField = TYPE_TO_FIELD[rawType] || null;

    ALL_TYPED_FIELDS.forEach(function (fieldName) {
      enableCell(rowFieldCell(row, fieldName), fieldName === keepField);
    });

    clearIrrelevantInputs(row, keepField);
  }

  function updateAllRows(container) {
    container.querySelectorAll("tr.form-row, tr.dynamic-metric_values, tr.has_original").forEach(updateRow);
  }

  function extractDatasetValue(option, keys) {
    for (const key of keys) {
      const val = option.dataset[key];
      if (val !== undefined && val !== null && String(val).trim() !== "") {
        return String(val).trim();
      }
    }
    return "";
  }

  function applyMetricDefinitionMetadata(row) {
    const metricSelect = rowMetricDefinitionSelect(row);
    if (!metricSelect) return;

    const option = metricSelect.options[metricSelect.selectedIndex];
    if (!option) return;

    const detectedType = extractDatasetValue(option, [
      "valueDataType",
      "valuedatatype",
      "type",
      "dataType",
      "datatype",
    ]).toLowerCase();

    const detectedUnits = extractDatasetValue(option, [
      "units",
      "unit",
    ]);

    const typeInput = rowValueTypeInput(row);
    const unitsInput = rowUnitsInput(row);

    if (typeInput && detectedType) {
      typeInput.value = detectedType;
      typeInput.dispatchEvent(new Event("change", { bubbles: true }));
    }

    if (unitsInput && detectedUnits && !String(unitsInput.value || "").trim()) {
      unitsInput.value = detectedUnits;
      unitsInput.dispatchEvent(new Event("change", { bubbles: true }));
    }

    updateRow(row);
  }

  function bind(container) {
    container.addEventListener("change", function (event) {
      const target = event.target;
      if (!target) return;

      if (target.name && target.name.endsWith("-value_data_type")) {
        const row = target.closest("tr");
        if (row) updateRow(row);
        return;
      }

      if (target.name && target.name.endsWith("-metric_definition")) {
        const row = target.closest("tr");
        if (row) applyMetricDefinitionMetadata(row);
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    const inlineGroup = document.getElementById("metric_values-group");
    if (!inlineGroup) return;

    bind(inlineGroup);
    updateAllRows(inlineGroup);

    const observer = new MutationObserver(function () {
      updateAllRows(inlineGroup);
    });

    observer.observe(inlineGroup, {
      childList: true,
      subtree: true,
    });
  });
})();