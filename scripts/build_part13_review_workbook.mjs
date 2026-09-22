import fs from "node:fs/promises";
import { SpreadsheetFile, Workbook } from "@oai/artifact-tool";

const root = "D:/app ai";
const queuePath = `${root}/reports/part13/ai_reviewed_queue.jsonl`;
const comparison = JSON.parse(await fs.readFile(`${root}/reports/part11/evaluation/comparison.json`, "utf8"));
const gate = JSON.parse(await fs.readFile(`${root}/reports/part12/release_gate.json`, "utf8"));
const rows = (await fs.readFile(queuePath, "utf8")).split(/\r?\n/).filter(Boolean).map(JSON.parse);
const outDir = `${root}/reports/part13`;
await fs.mkdir(outDir, { recursive: true });

const wb = Workbook.create();
const font = "Arial";

const summary = wb.worksheets.add("Summary");
summary.showGridLines = false;
summary.tabColor = "#1F4E78";
summary.getRange("A2:F2").merge();
summary.getRange("A2").values = [["TripMe Part 13 Human Review"]];
summary.getRange("A2").format.font = { name: font, size: 15, bold: true, color: "#1F2937" };
summary.getRange("A3:F3").format.borders = { bottom: { style: "thin", color: "#9CA3AF" } };
summary.getRange("A5:B13").values = [
  ["Review metric", "Value"],
  ["Evaluation rows", comparison.rows],
  ["Automatically flagged", comparison.flagged_rows],
  ["Passed samples included", comparison.sampled_pass_rows],
  ["Rows requiring review", comparison.human_review_rows],
  ["Metric gate", gate.metric_gate_passed ? "Passed" : "Failed"],
  ["Human decisions completed", null],
  ["Approved or edited", null],
  ["Release review status", null],
];
summary.getRange("B11").formulas = [[`=COUNTIF(Review!Q2:Q${rows.length + 1},"Approve")+COUNTIF(Review!Q2:Q${rows.length + 1},"Edit")+COUNTIF(Review!Q2:Q${rows.length + 1},"Reject")`]];
summary.getRange("B12").formulas = [[`=COUNTIF(Review!Q2:Q${rows.length + 1},"Approve")+COUNTIF(Review!Q2:Q${rows.length + 1},"Edit")`]];
summary.getRange("B13").formulas = [[`=IF(B11<B9,"Pending human review",IF(COUNTIF(Review!Q2:Q${rows.length + 1},"Reject")>0,"Rejected rows require action",IF(B10="Failed","Metric gate failed","Ready for release approval")))`]];
summary.getRange("A5:B5").format = { fill: "#1F4E78", font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
summary.getRange("A6:B13").format.font = { name: font, size: 10, color: "#1F2937" };
summary.getRange("A15:F20").values = [
  ["Review instructions", null, null, null, null, null],
  ["1", "Review all flagged rows first, then the sampled-pass rows.", null, null, null, null],
  ["2", "Choose Approve, Edit, or Reject in the Human decision column.", null, null, null, null],
  ["3", "For Edit, enter the corrected answer. Enter your name in Reviewer.", null, null, null, null],
  ["4", "Do not approve invented prices, opening status, accessibility guarantees, or corrupted text.", null, null, null, null],
  ["5", "A completed workbook does not override a failed metric gate; retraining may still be required.", null, null, null, null],
];
summary.getRange("A15:F15").merge();
summary.getRange("A15").format = { fill: "#D9EAF7", font: { name: font, size: 11, bold: true, color: "#1F2937" } };
summary.getRange("B16:F20").merge(true);
summary.getRange("A16:F20").format.font = { name: font, size: 10, color: "#1F2937" };
summary.getRange("A:A").format.columnWidth = 27;
summary.getRange("B:F").format.columnWidth = 21;

const review = wb.worksheets.add("Review");
review.showGridLines = false;
review.tabColor = "#5B9BD5";
const headers = ["Eval ID", "Priority", "Language", "Scenario", "Place names", "Prompt", "Reference answer", "Generated answer", "Automatic reasons", "Name coverage", "Scenario relevant", "Encoding clean", "Repetition", "AI recommendation", "AI rationale", "AI suggested answer", "Human decision", "Corrected answer", "Reviewer", "Review notes"];
const values = [headers];
for (const row of rows) {
  const c = row.automatic_checks;
  values.push([
    row.eval_id, row.review_priority, row.language, row.scenario,
    (row.target_place_names ?? []).join(", "), row.prompt, row.reference_answer,
    row.generated, (row.review_reasons ?? []).join(", "), c.place_name_coverage,
    c.scenario_relevance ? "Yes" : "No", c.encoding_clean ? "Yes" : "No",
    c.repetition_score, row.ai_recommendation, row.ai_rationale, row.ai_suggested_answer,
    "", "", "", "",
  ]);
}
review.getRange(`A1:T${values.length}`).write(values);
review.getRange("A1:T1").format = {
  fill: "#1F4E78", font: { name: font, size: 10, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "center", verticalAlignment: "center",
  borders: { preset: "inside", style: "thin", color: "#FFFFFF" },
};
review.getRange(`A2:T${values.length}`).format.font = { name: font, size: 9, color: "#1F2937" };
review.getRange(`E2:T${values.length}`).format.wrapText = true;
review.getRange(`E2:T${values.length}`).format.verticalAlignment = "top";
review.getRange(`N2:P${values.length}`).format.fill = "#D9EAF7";
review.getRange(`Q2:T${values.length}`).format.fill = "#FFF2CC";
review.getRange(`Q2:Q${values.length}`).dataValidation = { rule: { type: "list", values: ["Approve", "Edit", "Reject"] } };
review.getRange(`Q2:Q${values.length}`).conditionalFormats.add("containsText", { text: "Approve", format: { fill: "#E2F0D9", font: { color: "#276221", bold: true } } });
review.getRange(`Q2:Q${values.length}`).conditionalFormats.add("containsText", { text: "Edit", format: { fill: "#FFF2CC", font: { color: "#8A4B08", bold: true } } });
review.getRange(`Q2:Q${values.length}`).conditionalFormats.add("containsText", { text: "Reject", format: { fill: "#FCE8E6", font: { color: "#B91C1C", bold: true } } });
review.getRange(`B2:B${values.length}`).conditionalFormats.add("containsText", { text: "flagged", format: { fill: "#FCE8E6", font: { color: "#B91C1C", bold: true } } });
review.getRange(`J2:J${values.length}`).format.numberFormat = "0.0%";
review.getRange(`M2:M${values.length}`).format.numberFormat = "0.000";
review.freezePanes.freezeRows(1);
review.freezePanes.freezeColumns(5);
const widths = { A: 13, B: 14, C: 10, D: 23, E: 30, F: 45, G: 48, H: 48, I: 25, J: 13, K: 14, L: 12, M: 12, N: 17, O: 38, P: 48, Q: 16, R: 48, S: 18, T: 30 };
for (const [col, width] of Object.entries(widths)) review.getRange(`${col}:${col}`).format.columnWidth = width;
review.getRange("1:1").format.rowHeight = 30;
review.getRange(`2:${values.length}`).format.rowHeight = 92;
review.tables.add(`A1:T${values.length}`, true, "HumanReviewTable");

const metrics = wb.worksheets.add("Metrics");
metrics.showGridLines = false;
metrics.getRange("A2:E2").merge();
metrics.getRange("A2").values = [["Evaluation metric comparison"]];
metrics.getRange("A2").format.font = { name: font, size: 14, bold: true, color: "#1F2937" };
metrics.getRange("A4:E10").values = [
  ["Metric", "Part 6", "Part 8", "Part 11", "Part 12 gate"],
  ["Complete ending rate", comparison.part6.complete_ending_rate, comparison.part8.complete_ending_rate, comparison.part11.complete_ending_rate, gate.metric_checks.complete_ending_rate ? "Pass" : "Fail"],
  ["Token-limit hit rate", comparison.part6.token_limit_hit_rate, comparison.part8.token_limit_hit_rate, comparison.part11.token_limit_hit_rate, gate.metric_checks.token_limit_hit_rate ? "Pass" : "Fail"],
  ["Place-name coverage", comparison.part6.mean_place_name_coverage, comparison.part8.mean_place_name_coverage, comparison.part11.mean_place_name_coverage, gate.metric_checks.place_name_coverage ? "Pass" : "Fail"],
  ["Scenario relevance", null, comparison.part8.scenario_relevance_rate, comparison.part11.scenario_relevance_rate, gate.metric_checks.scenario_relevance_rate ? "Pass" : "Fail"],
  ["Encoding clean rate", null, comparison.part8.encoding_clean_rate, comparison.part11.encoding_clean_rate, gate.metric_checks.encoding_clean_rate ? "Pass" : "Fail"],
  ["Mean repetition", comparison.part6.mean_repetition_score, comparison.part8.mean_repetition_score, comparison.part11.mean_repetition_score, gate.metric_checks.repetition_score ? "Pass" : "Fail"],
];
metrics.getRange("A4:E4").format = { fill: "#1F4E78", font: { name: font, size: 10, bold: true, color: "#FFFFFF" }, horizontalAlignment: "center" };
metrics.getRange("A5:E10").format.font = { name: font, size: 10, color: "#1F2937" };
metrics.getRange("B5:D10").format.numberFormat = "0.0%";
metrics.getRange("E5:E10").conditionalFormats.add("containsText", { text: "Fail", format: { fill: "#FCE8E6", font: { color: "#B91C1C", bold: true } } });
metrics.getRange("A:A").format.columnWidth = 28;
metrics.getRange("B:D").format.columnWidth = 14;
metrics.getRange("E:E").format.columnWidth = 18;

wb.recalculate();
const inspect = await wb.inspect({ kind: "table", range: "Summary!A1:F20", include: "values,formulas", tableMaxRows: 22, tableMaxCols: 8 });
console.log(inspect.ndjson);
const errors = await wb.inspect({ kind: "match", searchTerm: "#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!", options: { useRegex: true, maxResults: 100 }, summary: "final formula error scan" });
console.log(errors.ndjson);
const output = await SpreadsheetFile.exportXlsx(wb);
await output.save(`${outDir}/tripme_part13_ai_reviewed.xlsx`);
console.log(`${outDir}/tripme_part13_ai_reviewed.xlsx`);
