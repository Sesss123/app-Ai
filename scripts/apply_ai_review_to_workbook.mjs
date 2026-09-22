import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "D:/app ai/data/training/pilot_v0.2.0/review";
const sourcePath = `${root}/tripme_pilot_ai_reviewed_v0.2.0.xlsx`;
const outputPath = `${root}/tripme_pilot_second_checked_v0.2.0.xlsx`;
const payload = JSON.parse(await fs.readFile(`${root}/second_check_records.json`, "utf8"));
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourcePath));

const summary = workbook.worksheets.getItem("Summary");
summary.getRange("B10").values = [["AI second check complete; human review required"]];
summary.getRange("A19:B23").values = [
  ["AI second-check summary", "Count"],
  ["Approve", payload.decisions.Approve ?? 0],
  ["Edit", payload.decisions.Edit ?? 0],
  ["Reject", payload.decisions.Reject ?? 0],
  ["Status", "Candidate only — not human-reviewed"],
];
summary.getRange("A19:B19").format = {
  fill: "#1F4E78",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
};
summary.getRange("A20:B23").format.font = { name: "Arial", size: 10, color: "#1F2937" };
summary.getRange("A20:A23").format.font = { name: "Arial", size: 10, bold: true, color: "#1F4E78" };
summary.getRange("B:B").format.columnWidth = 42;

for (let batch = 0; batch < 10; batch++) {
  const sheet = workbook.worksheets.getItem(`Batch ${String(batch + 1).padStart(2, "0")}`);
  const records = payload.reviews.slice(batch * 100, batch * 100 + 100);
  const values = records.map((r) => [
    r.decision,
    r.edited_prompt,
    r.edited_answer,
    r.reviewer,
    r.notes,
  ]);
  sheet.getRange(`G2:K${records.length + 1}`).values = values;
}

workbook.recalculate();
const summaryInspect = await workbook.inspect({
  kind: "table",
  sheetId: "Summary",
  range: "A5:B23",
  include: "values,formulas",
  tableMaxRows: 25,
  tableMaxCols: 4,
  maxChars: 8000,
});
console.log(summaryInspect.ndjson);
const errorScan = await workbook.inspect({
  kind: "match",
  searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!",
  options: { useRegex: true, maxResults: 100 },
  summary: "formula error scan before export",
});
console.log(errorScan.ndjson);

const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
