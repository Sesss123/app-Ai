import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const path = "D:/app ai/data/training/corrective_v0.3.0/tripme_part07_corrective_ai_reviewed_v0.3.0.xlsx";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 5000 });
console.log(sheets.ndjson);
const summary = await workbook.inspect({ kind: "table", sheetId: "Summary", range: "A5:B27", include: "values,formulas", tableMaxRows: 25, tableMaxCols: 4, maxChars: 9000 });
console.log(summary.ndjson);
const first = await workbook.inspect({ kind: "table", sheetId: "Batch 01", range: "A1:L4", include: "values,formulas", tableMaxRows: 4, tableMaxCols: 12, maxChars: 10000 });
console.log(first.ndjson);
const last = await workbook.inspect({ kind: "table", sheetId: "Batch 11", range: "A48:L51", include: "values,formulas", tableMaxRows: 5, tableMaxCols: 12, maxChars: 10000 });
console.log(last.ndjson);
const editOne = await workbook.inspect({ kind: "table", sheetId: "Batch 08", range: "A59:L59", include: "values,formulas", tableMaxRows: 2, tableMaxCols: 12, maxChars: 6000 });
console.log(editOne.ndjson);
const editTwo = await workbook.inspect({ kind: "table", sheetId: "Batch 11", range: "A39:L39", include: "values,formulas", tableMaxRows: 2, tableMaxCols: 12, maxChars: 6000 });
console.log(editTwo.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "saved workbook error scan" });
console.log(errors.ndjson);
