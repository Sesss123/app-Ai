import fs from "node:fs/promises";
import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const root = "D:/app ai/data/training/corrective_v0.3.0";
const sourcePath = `${root}/tripme_part07_corrective_review_v0.3.0.xlsx`;
const outputPath = `${root}/tripme_part07_corrective_ai_reviewed_v0.3.0.xlsx`;
const payload = JSON.parse(await fs.readFile(`${root}/ai_review_records.json`, "utf8"));
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(sourcePath));

const summary = workbook.worksheets.getItem("Summary");
summary.getRange("B14").values = [["AI second-pass complete; human review still required"]];
summary.getRange("A23:B27").values = [
  ["AI review summary", "Count"],
  ["Approve", payload.decisions.Approve ?? 0],
  ["Edit", payload.decisions.Edit ?? 0],
  ["Reject", payload.decisions.Reject ?? 0],
  ["Status", "Candidate only — not human-reviewed"],
];
summary.getRange("A23:B23").format = {
  fill: "#1F4E78",
  font: { name: "Arial", size: 10, bold: true, color: "#FFFFFF" },
};
summary.getRange("A24:B27").format.font = { name: "Arial", size: 10, color: "#1F2937" };
summary.getRange("A24:A27").format.font = { name: "Arial", size: 10, bold: true, color: "#1F4E78" };
summary.getRange("B:B").format.columnWidth = 46;

const batchSize = 100;
for (let batch = 0; batch < 11; batch++) {
  const sheet = workbook.worksheets.getItem(`Batch ${String(batch + 1).padStart(2, "0")}`);
  const records = payload.reviews.slice(batch * batchSize, (batch + 1) * batchSize);
  const values = records.map((row) => [
    row.decision, row.edited_prompt, row.edited_answer, row.reviewer, row.notes,
  ]);
  sheet.getRange(`H2:L${records.length + 1}`).values = values;
}

workbook.recalculate();
const summaryInspect = await workbook.inspect({ kind: "table", sheetId: "Summary", range: "A5:B27", include: "values,formulas", tableMaxRows: 25, tableMaxCols: 4, maxChars: 9000 });
console.log(summaryInspect.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "formula error scan before export" });
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);
console.log(outputPath);
