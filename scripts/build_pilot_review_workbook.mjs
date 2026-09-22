import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "D:/app ai";
const inputFiles = [
  `${root}/data/training/pilot_v0.2.0/pilot_train_draft.jsonl`,
  `${root}/data/training/pilot_v0.2.0/pilot_validation_draft.jsonl`,
];
const outputDir = `${root}/data/training/pilot_v0.2.0/review`;

const rows = [];
for (const path of inputFiles) {
  const text = await fs.readFile(path, "utf8");
  for (const line of text.split(/\r?\n/)) {
    if (line.trim()) rows.push(JSON.parse(line));
  }
}

const workbook = Workbook.create();
const summary = workbook.worksheets.add("Summary");
summary.showGridLines = false;
summary.tabColor = "#1F4E78";
summary.getRange("A2:F2").merge();
summary.getRange("A2").values = [["TripMe Pilot Dataset Review"]];
summary.getRange("A2").format.font = { name: "Arial", size: 15, bold: true, color: "#1F2937" };
summary.getRange("A3:F3").format.borders = { bottom: { style: "thin", color: "#9CA3AF" } };
summary.getRange("A5:B10").values = [
  ["Metric", "Value"],
  ["Examples", rows.length],
  ["Batches", 10],
  ["Rows per batch", 100],
  ["Automated quality gate", "Passed"],
  ["Human review status", "Pending"],
];
summary.getRange("A5:B5").format = { fill: "#1F4E78", font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" } };
summary.getRange("A6:B10").format.font = { name: "Arial", size: 10, color: "#1F2937" };
summary.getRange("A12:F17").values = [
  ["Review instructions", null, null, null, null, null],
  ["1", "Read the user prompt and assistant answer in each Batch tab.", null, null, null, null],
  ["2", "Choose Approve, Edit, or Reject in the Decision column.", null, null, null, null],
  ["3", "For Edit, enter corrected text in Edited Prompt and/or Edited Answer.", null, null, null, null],
  ["4", "Enter reviewer name and concise notes for edits or rejections.", null, null, null, null],
  ["5", "Do not approve unsupported current price, opening, weather, road, or safety claims.", null, null, null, null],
];
summary.getRange("A12:F12").merge();
summary.getRange("A12").format = { fill: "#D9EAF7", font: { name: "Arial", size: 11, bold: true, color: "#1F2937" } };
summary.getRange("A13:A17").format.font = { name: "Arial", bold: true, color: "#1F4E78" };
summary.getRange("B13:F17").merge(true);
summary.getRange("A13:F17").format.font = { name: "Arial", size: 10, color: "#1F2937" };
summary.getRange("A1:F20").format.verticalAlignment = "center";
summary.getRange("A:A").format.columnWidth = 18;
summary.getRange("B:F").format.columnWidth = 19;

const headers = ["Review ID", "Language", "Scenario", "Place IDs", "User Prompt", "Assistant Answer", "Decision", "Edited Prompt", "Edited Answer", "Reviewer", "Notes"];
for (let batch = 0; batch < 10; batch++) {
  const sheet = workbook.worksheets.add(`Batch ${String(batch + 1).padStart(2, "0")}`);
  sheet.showGridLines = false;
  const batchRows = rows.slice(batch * 100, batch * 100 + 100);
  const values = [headers];
  for (let index = 0; index < batchRows.length; index++) {
    const item = batchRows[index];
    const user = item.messages.find((m) => m.role === "user")?.content ?? "";
    const assistant = item.messages.find((m) => m.role === "assistant")?.content ?? "";
    values.push([
      `pilot-${String(batch * 100 + index + 1).padStart(4, "0")}`,
      item.lang,
      item.scenario,
      JSON.stringify(item.place_ids),
      user,
      assistant,
      "",
      "",
      "",
      "",
      "",
    ]);
  }
  sheet.getRange("A1").write(values);
  sheet.getRange("A1:K1").format = {
    fill: "#1F4E78",
    font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
  };
  sheet.getRange("A2:K101").format.font = { name: "Arial", size: 9, color: "#1F2937" };
  sheet.getRange("A2:D101").format.verticalAlignment = "center";
  sheet.getRange("E2:K101").format.verticalAlignment = "top";
  sheet.getRange("E2:K101").format.wrapText = true;
  sheet.getRange("G2:K101").format.fill = "#FFF2CC";
  sheet.getRange("G2:G101").dataValidation = { rule: { type: "list", values: ["Approve", "Edit", "Reject"] } };
  sheet.getRange("G2:G101").conditionalFormats.add("containsText", { text: "Reject", format: { fill: "#FCE8E6", font: { color: "#B91C1C", bold: true } } });
  sheet.getRange("G2:G101").conditionalFormats.add("containsText", { text: "Approve", format: { fill: "#E2F0D9", font: { color: "#276221", bold: true } } });
  sheet.getRange("G2:G101").conditionalFormats.add("containsText", { text: "Edit", format: { fill: "#FFF2CC", font: { color: "#8A4B08", bold: true } } });
  sheet.freezePanes.freezeRows(1);
  sheet.freezePanes.freezeColumns(4);
  sheet.getRange("A:A").format.columnWidth = 13;
  sheet.getRange("B:B").format.columnWidth = 10;
  sheet.getRange("C:C").format.columnWidth = 22;
  sheet.getRange("D:D").format.columnWidth = 27;
  sheet.getRange("E:F").format.columnWidth = 48;
  sheet.getRange("G:G").format.columnWidth = 12;
  sheet.getRange("H:I").format.columnWidth = 48;
  sheet.getRange("J:J").format.columnWidth = 16;
  sheet.getRange("K:K").format.columnWidth = 28;
  sheet.getRange("1:1").format.rowHeight = 28;
  sheet.getRange("2:101").format.rowHeight = 72;
  sheet.tables.add("A1:K101", true, `ReviewBatch${batch + 1}`);
}

workbook.recalculate();
await fs.mkdir(outputDir, { recursive: true });

const summaryInspect = await workbook.inspect({ kind: "table", sheetId: "Summary", range: "A1:F18", include: "values,formulas", tableMaxRows: 20, tableMaxCols: 12 });
console.log(summaryInspect.ndjson);
const errorScan = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan" });
console.log(errorScan.ndjson);

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(`${outputDir}/tripme_pilot_review_v0.2.0.xlsx`);
console.log(`${outputDir}/tripme_pilot_review_v0.2.0.xlsx`);
