import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const path = "D:/app ai/data/training/pilot_v0.2.0/review/tripme_pilot_second_checked_v0.2.0.xlsx";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 });
console.log(sheets.ndjson);
const summary = await workbook.inspect({ kind: "table", sheetId: "Summary", range: "A5:B23", include: "values,formulas", tableMaxRows: 25, tableMaxCols: 4, maxChars: 8000 });
console.log(summary.ndjson);
const first = await workbook.inspect({ kind: "table", sheetId: "Batch 01", range: "A1:K6", include: "values,formulas", tableMaxRows: 6, tableMaxCols: 11, maxChars: 12000 });
console.log(first.ndjson);
const last = await workbook.inspect({ kind: "table", sheetId: "Batch 10", range: "A97:K101", include: "values,formulas", tableMaxRows: 6, tableMaxCols: 11, maxChars: 12000 });
console.log(last.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "saved workbook error scan" });
console.log(errors.ndjson);
