import { FileBlob, SpreadsheetFile } from "@oai/artifact-tool";

const path = "D:/app ai/data/training/pilot_v0.2.0/review/tripme_pilot_review_v0.2.0.xlsx";
const workbook = await SpreadsheetFile.importXlsx(await FileBlob.load(path));
const sheets = await workbook.inspect({ kind: "sheet", include: "id,name", maxChars: 4000 });
console.log(sheets.ndjson);
const batch = await workbook.inspect({ kind: "table", sheetId: "Batch 01", range: "A1:K6", include: "values,formulas", tableMaxRows: 6, tableMaxCols: 11, maxChars: 6000 });
console.log(batch.ndjson);
const errors = await workbook.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "saved workbook error scan" });
console.log(errors.ndjson);
