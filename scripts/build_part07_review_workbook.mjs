import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "D:/app ai/data/training/corrective_v0.3.0";
const sources = [
  ["train", `${root}/corrective_train_draft.jsonl`],
  ["validation", `${root}/corrective_validation_draft.jsonl`],
];
const rows = [];
for (const [split, path] of sources) {
  const text = await fs.readFile(path, "utf8");
  for (const line of text.split(/\r?\n/)) {
    if (line.trim()) rows.push({ split, ...JSON.parse(line) });
  }
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
summary.showGridLines = false;
summary.tabColor = "#1F4E78";
summary.getRange("A2:F2").merge();
summary.getRange("A2").values = [["TripMe Part 7 Corrective Data Review"]];
summary.getRange("A2").format.font = { name: "Arial", size: 15, bold: true, color: "#1F2937" };
summary.getRange("A3:F3").format.borders = { bottom: { style: "thin", color: "#9CA3AF" } };
summary.getRange("A5:B14").values = [
  ["Metric", "Value"],
  ["Corrective examples", rows.length],
  ["Train examples", 900],
  ["Validation examples", 150],
  ["Sinhala", 840],
  ["Singlish", 105],
  ["English", 105],
  ["Train/validation place overlap", 0],
  ["Gold holdout overlap", 0],
  ["Human review status", "Pending"],
];
summary.getRange("A5:B5").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
summary.getRange("A6:B14").format.font = { name: "Arial", size: 10, color: "#1F2937" };
summary.getRange("A16:F21").values = [
  ["Review instructions", null, null, null, null, null],
  ["1", "Review every generated prompt and answer, focusing first on Sinhala naturalness.", null, null, null, null],
  ["2", "Choose Approve, Edit, or Reject in each batch tab.", null, null, null, null],
  ["3", "For Edit, enter only the corrected prompt and/or answer.", null, null, null, null],
  ["4", "Reject unsupported prices, opening claims, accessibility guarantees, or invented rules.", null, null, null, null],
  ["5", "Keep the exact place name and do not mark this dataset human-reviewed until completed.", null, null, null, null],
];
summary.getRange("A16:F16").merge();
summary.getRange("A16").format = { fill: "#D9EAF7", font: { name: "Arial", size: 11, bold: true, color: "#1F2937" } };
summary.getRange("B17:F21").merge(true);
summary.getRange("A17:A21").format.font = { name: "Arial", bold: true, color: "#1F4E78" };
summary.getRange("A17:F21").format.font = { name: "Arial", size: 10, color: "#1F2937" };
summary.getRange("A:A").format.columnWidth = 26;
summary.getRange("B:F").format.columnWidth = 20;

const headers = ["Review ID", "Split", "Language", "Scenario", "Place IDs", "User Prompt", "Assistant Answer", "Decision", "Edited Prompt", "Edited Answer", "Reviewer", "Notes"];
const batchSize = 100;
const batchCount = Math.ceil(rows.length / batchSize);
for (let batch = 0; batch < batchCount; batch++) {
  const sheet = workbook.worksheets.add(`Batch ${String(batch + 1).padStart(2, "0")}`);
  sheet.showGridLines = false;
  const batchRows = rows.slice(batch * batchSize, (batch + 1) * batchSize);
  const values = [headers];
  for (let index = 0; index < batchRows.length; index++) {
    const item = batchRows[index];
    const user = item.messages.find((m) => m.role === "user")?.content ?? "";
    const assistant = item.messages.find((m) => m.role === "assistant")?.content ?? "";
    values.push([
      `corrective-${String(batch * batchSize + index + 1).padStart(4, "0")}`,
      item.split,
      item.lang,
      item.scenario,
      JSON.stringify(item.place_ids),
      user,
      assistant,
      "", "", "", "", "",
    ]);
  }
  const lastRow = batchRows.length + 1;
  sheet.getRange("A1").write(values);
  sheet.getRange("A1:L1").format = {
    fill: "#1F4E78",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center", verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  sheet.getRange(`A2:L${lastRow}`).format.font = { name: "Arial", size: 9, color: "#1F2937" };
  sheet.getRange(`F2:L${lastRow}`).format.wrapText = true;
  sheet.getRange(`F2:L${lastRow}`).format.verticalAlignment = "top";
  sheet.getRange(`H2:L${lastRow}`).format.fill = "#FFF2CC";
  sheet.getRange(`H2:H${lastRow}`).dataValidation = { rule: { type: "list", values: ["Approve", "Edit", "Reject"] } };
  sheet.getRange(`H2:H${lastRow}`).conditionalFormats.add("containsText", { text: "Approve", format: { fill: "#E2F0D9", font: { color: "#276221", bold: true } } });
  sheet.getRange(`H2:H${lastRow}`).conditionalFormats.add("containsText", { text: "Edit", format: { fill: "#FFF2CC", font: { color: "#8A4B08", bold: true } } });
  sheet.getRange(`H2:H${lastRow}`).conditionalFormats.add("containsText", { text: "Reject", format: { fill: "#FCE8E6", font: { color: "#B91C1C", bold: true } } });
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(5);
  sheet.getRange("A:A").format.columnWidth = 15;
  sheet.getRange("B:C").format.columnWidth = 11;
  sheet.getRange("D:D").format.columnWidth = 23;
  sheet.getRange("E:E").format.columnWidth = 25;
  sheet.getRange("F:G").format.columnWidth = 50;
  sheet.getRange("H:H").format.columnWidth = 12;
  sheet.getRange("I:J").format.columnWidth = 50;
  sheet.getRange("K:K").format.columnWidth = 17;
  sheet.getRange("L:L").format.columnWidth = 30;
  sheet.getRange("1:1").format.rowHeight = 28;
  sheet.getRange(`2:${lastRow}`).format.rowHeight = 78;
  sheet.tables.add(`A1:L${lastRow}`, true, `CorrectiveBatch${batch + 1}`);
}

workbook.recalculate();
const inspect = await workbook.inspect({ kind: "table", sheetId: "Summary", range: "A1:F21", include: "values,formulas", tableMaxRows: 24, tableMaxCols: 8, maxChars: 8000 });
console.log(inspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" });
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${root}/tripme_part07_corrective_review_v0.3.0.xlsx`);
console.log(`${root}/tripme_part07_corrective_review_v0.3.0.xlsx`);
