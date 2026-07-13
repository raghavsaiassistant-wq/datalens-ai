"""
pbix_real_export.py — Build a real .pbit file from analysis results.

Uses the well-tested pbi-tools sample (calc-groups) as a base, replaces
the data table and visuals with Sir's data, and compiles to .pbit.
"""
import os
import json
import shutil
import subprocess
import tempfile
import logging
import hashlib
import urllib.request
import zipfile

logger = logging.getLogger("PbixRealExport")

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PBI_TOOLS_EXE = os.path.join(BACKEND_DIR, "pbi-tools", "pbi-tools.core.exe")

SAMPLE_REPO_URL = "https://github.com/pbi-tools/pbi-tools/archive/refs/heads/main.zip"
SAMPLE_DIR_NAME = "calc-groups"
SAMPLE_CACHE = os.path.join(BACKEND_DIR, ".pbix-sample-cache")


def _ensure_sample() -> str:
    """Download and extract the pbi-tools sample, return path to the PbixProj folder."""
    if os.path.exists(SAMPLE_CACHE) and os.path.exists(os.path.join(SAMPLE_CACHE, ".pbixproj.json")):
        return SAMPLE_CACHE

    os.makedirs(SAMPLE_CACHE, exist_ok=True)
    zip_path = os.path.join(BACKEND_DIR, "pbi-tools-master.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    logger.info(f"Downloading pbi-tools repo to get sample PbixProj...")
    req = urllib.request.Request(SAMPLE_REPO_URL, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        zip_data = r.read()
    with open(zip_path, "wb") as f:
        f.write(zip_data)
    logger.info(f"Extracting {SAMPLE_DIR_NAME}...")
    with zipfile.ZipFile(zip_path) as zf:
        names = zf.namelist()
        prefix = None
        for n in names:
            if n.endswith(f"/data/Samples/{SAMPLE_DIR_NAME}/.pbixproj.json"):
                prefix = n.rsplit(f"/data/Samples/{SAMPLE_DIR_NAME}/.pbixproj.json", 1)[0] + f"/data/Samples/{SAMPLE_DIR_NAME}/"
                break
        if not prefix:
            for n in names:
                if f"/data/Samples/{SAMPLE_DIR_NAME}/" in n and not n.endswith("/"):
                    prefix = n.split(f"/data/Samples/{SAMPLE_DIR_NAME}/", 1)[0] + f"/data/Samples/{SAMPLE_DIR_NAME}/"
                    break
        if not prefix:
            raise RuntimeError(f"Could not find calc-groups folder")
        logger.info(f"Using prefix: {prefix}")
        for name in names:
            if name.startswith(prefix) and not name.endswith("/"):
                rel = name[len(prefix):]
                target = os.path.join(SAMPLE_CACHE, rel)
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(name) as src, open(target, "wb") as dst:
                    dst.write(src.read())
    if os.path.exists(zip_path):
        os.remove(zip_path)
    return SAMPLE_CACHE


def build_pbix(analysis_result: dict, session_id: str, output_dir: str = None) -> str:
    if output_dir is None:
        output_dir = tempfile.mkdtemp(prefix="datalens_pbix_")
    os.makedirs(output_dir, exist_ok=True)
    workdir = os.path.join(output_dir, "proj")
    if os.path.exists(workdir):
        shutil.rmtree(workdir)

    sample = _ensure_sample()
    shutil.copytree(sample, workdir)
    logger.info(f"Project dir: {workdir}")

    records = analysis_result.get("records", [])
    if not records:
        records = _records_from_charts(analysis_result.get("charts", []))
    if not records:
        raise ValueError("No records available to build .pbix")
    columns = analysis_result.get("records_columns") or list(records[0].keys())
    columns = _clean_column_names(columns)
    records = _clean_records(records, columns)
    table_name = "Data"

    csv_path = os.path.join(workdir, "data.csv")
    _write_csv(csv_path, records, columns)

    _rewrite_model(workdir, table_name, columns, records, analysis_result)
    _replace_report(workdir, table_name, columns, analysis_result)
    _write_linguistic_schema(os.path.join(workdir, "LinguisticSchema.xml"), table_name, columns)

    with open(os.path.join(workdir, "Version.txt"), "w") as f:
        f.write("1.20")

    output_pbit = os.path.join(output_dir, f"datalens-dashboard-{session_id[:8]}.pbit")
    cmd = [PBI_TOOLS_EXE, "compile", workdir, output_pbit, "PBIT", "Overwrite"]
    logger.info(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        logger.error(f"pbi-tools compile failed:\nSTDOUT: {result.stdout[:2000]}\nSTDERR: {result.stderr[:500]}")
        raise RuntimeError(f"pbi-tools compile failed: {result.stdout[-500:]}")

    if not os.path.exists(output_pbit):
        raise FileNotFoundError(f"pbi-tools did not produce output: {output_pbit}")

    size = os.path.getsize(output_pbit)
    logger.info(f"Generated: {output_pbit} ({size:,} bytes)")
    return output_pbit


def _records_from_charts(charts):
    out = []
    for c in charts:
        if not isinstance(c, dict) or not c.get("data"):
            continue
        for pt in c["data"]:
            row = {}
            if c.get("x_col"):
                row[c["x_col"]] = pt.get("x")
            if c.get("y_col"):
                row[c["y_col"]] = pt.get("y")
            if row:
                out.append(row)
    return out


def _clean_column_names(cols):
    return [str(c).strip() or "Column" for c in cols]


def _clean_records(records, columns):
    import math
    cleaned = []
    for r in records:
        new_r = {}
        for c in columns:
            v = r.get(c)
            if v is None:
                new_r[c] = None
            elif isinstance(v, bool):
                new_r[c] = v
            elif isinstance(v, (int, float)):
                if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
                    new_r[c] = None
                else:
                    new_r[c] = v
            else:
                new_r[c] = str(v)
        cleaned.append(new_r)
    return cleaned


def _write_csv(path, records, columns):
    with open(path, "w", newline="", encoding="utf-8") as f:
        f.write(",".join(_csv_escape(c) for c in columns) + "\n")
        for rec in records:
            row_vals = []
            for col in columns:
                val = rec.get(col)
                if val is None or val == "":
                    row_vals.append("")
                elif isinstance(val, (int, float, bool)):
                    row_vals.append(str(val))
                else:
                    row_vals.append(_csv_escape(str(val)))
            f.write(",".join(row_vals) + "\n")


def _csv_escape(s):
    if any(c in s for c in [",", '"', "\n", "\r"]):
        return '"' + s.replace('"', '""') + '"'
    return s


def _rewrite_model(workdir, table_name, columns, records, analysis_result):
    col_defs = []
    for col in columns:
        sample_vals = [r.get(col) for r in records[:50] if r.get(col) is not None]
        if not sample_vals:
            data_type = "string"
            fmt_annotation = "Text"
            type_annotation = "String#####not a type"
        elif all(isinstance(v, bool) for v in sample_vals):
            data_type = "boolean"
            fmt_annotation = "General"
            type_annotation = "Boolean#####not a type"
        elif all(isinstance(v, int) for v in sample_vals):
            data_type = "int64"
            fmt_annotation = "General"
            type_annotation = "Int64#####not a type"
        elif all(isinstance(v, (int, float)) for v in sample_vals):
            data_type = "double"
            fmt_annotation = "General"
            type_annotation = "Double#####not a type"
        else:
            data_type = "string"
            fmt_annotation = "Text"
            type_annotation = "String#####not a type"

        col_defs.append({
            "name": col,
            "dataType": data_type,
            "isHidden": False,
            "sourceColumn": col,
            "summarizeBy": "none",
            "annotations": [
                {"name": "Format", "value": f"<Format Format=\"{fmt_annotation}\" />"},
                {"name": "DataTypeAtRefresh", "value": type_annotation},
                {"name": "SummarizationSetBy", "value": "Automatic"}
            ]
        })

    numeric_cols = [c["name"] for c in col_defs if c["dataType"] in ("int64", "double")]
    measures = []
    for col in numeric_cols[:5]:
        safe = col.replace("'", "''")
        measures.extend([
            {"name": f"Total {col}", "expression": f"SUM('{table_name}'[{col}])", "formatString": "#,0.00"},
            {"name": f"Avg {col}", "expression": f"AVERAGE('{table_name}'[{col}])", "formatString": "#,0.00"},
            {"name": f"Count {col}", "expression": f"COUNT('{table_name}'[{col}])", "formatString": "#,0"},
            {"name": f"Max {col}", "expression": f"MAX('{table_name}'[{col}])", "formatString": "#,0.00"},
            {"name": f"Min {col}", "expression": f"MIN('{table_name}'[{col}])", "formatString": "#,0.00"},
        ])

    partition = {
        "name": table_name,
        "mode": "import",
        "source": {
            "type": "m",
            "expression": [
                "let",
                "    Source = Csv.Document(File.Contents(\"data.csv\"),[Delimiter=\",\", Columns=" + str(len(columns)) + ", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),",
                "    PromoteHeaders = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
                "    ChangedTypes = Table.TransformColumnTypes(PromoteHeaders, " + json.dumps(_m_type_list(columns, records)) + "),",
                "    RenamedColumns = Table.RenameColumns(ChangedTypes, " + json.dumps([[c, c] for c in columns]) + ")",
                "in",
                "    RenamedColumns"
            ]
        }
    }

    database = {
        "name": "DataLensModel",
        "compatibilityLevel": 1520,
        "model": {
            "culture": "en-US",
            "dataAccessOptions": {"legacyRedirects": True, "returnErrorValuesAsNull": True},
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "discourageImplicitMeasures": True,
            "sourceQueryCulture": "en-US",
            "tables": [{
                "name": table_name,
                "columns": col_defs,
                "measures": measures,
                "partitions": [partition],
                "hierarchies": [],
                "annotations": []
            }],
            "relationships": [],
            "cultures": [{
                "name": "en-US",
                "linguisticMetadata": {
                    "contentType": "json",
                    "content": '{"Version":"1.0.0","Language":"en-US","Words":[],"Synonyms":[]}'
                }
            }],
            "expressions": [],
            "annotations": []
        }
    }

    os.makedirs(os.path.join(workdir, "Model"), exist_ok=True)
    with open(os.path.join(workdir, "Model", "database.json"), "w", encoding="utf-8") as f:
        json.dump(database, f, indent=2)
    with open(os.path.join(workdir, "Model", "expressions.json"), "w") as f:
        json.dump({"version": "1.0", "expressions": []}, f)


def _m_type_list(columns, records):
    types = []
    for col in columns:
        sample = [r.get(col) for r in records[:20] if r.get(col) is not None]
        if not sample:
            m_type = "type text"
        elif all(isinstance(v, bool) for v in sample):
            m_type = "type logical"
        elif all(isinstance(v, int) for v in sample):
            m_type = "Int64.Type"
        elif all(isinstance(v, (int, float)) for v in sample):
            m_type = "type number"
        else:
            m_type = "type text"
        types.append({"Column": col, "Type": m_type})
    return types


def _replace_report(workdir, table_name, columns, analysis_result):
    numeric_cols = [c for c in columns if c.lower() in
                    ("revenue", "sales", "amount", "value", "total", "price", "units", "quantity", "count", "score")]
    date_cols = [c for c in columns if "date" in c.lower() or "time" in c.lower() or "month" in c.lower()]
    cat_cols = [c for c in columns if c not in (numeric_cols + date_cols) and c.lower() not in
                ("id", "uuid", "key", "#", "index")]
    y_col = numeric_cols[0] if numeric_cols else (columns[1] if len(columns) > 1 else columns[0])
    date_col = date_cols[0] if date_cols else None
    cat_col = cat_cols[0] if cat_cols else (columns[0] if columns else y_col)

    sections_dir = os.path.join(workdir, "Report", "sections")
    if os.path.exists(sections_dir):
        shutil.rmtree(sections_dir)
    os.makedirs(sections_dir, exist_ok=True)

    with open(os.path.join(workdir, "Report", "report.json"), "w") as f:
        json.dump({
            "version": "1.0",
            "config": {"name": "DataLens Dashboard", "pages": ["Overview", "Details"]}
        }, f, indent=2)
    with open(os.path.join(workdir, "Report", "config.json"), "w") as f:
        json.dump({"version": "1.0"}, f, indent=2)

    _build_page_overview(sections_dir, "000_Overview", table_name, columns,
                          y_col, date_col, cat_col, cat_cols, analysis_result)
    _build_page_details(sections_dir, "001_Details", table_name, columns)


def _build_page_overview(sections_dir, section_id, table_name, columns,
                          y_col, date_col, cat_col, cat_cols, analysis_result):
    section_dir = os.path.join(sections_dir, section_id)
    os.makedirs(section_dir, exist_ok=True)
    os.makedirs(os.path.join(section_dir, "visualContainers"), exist_ok=True)

    with open(os.path.join(section_dir, "section.json"), "w") as f:
        json.dump({"name": "Overview", "displayName": "Overview", "ordinal": 0}, f, indent=2)
    with open(os.path.join(section_dir, "config.json"), "w") as f:
        f.write("{}")
    with open(os.path.join(section_dir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f, indent=2)

    _add_textbox(section_dir, "01", "📊 DataLens Dashboard — Overview", 0, 0, 1280, 60, fontSize=22, bold=True)
    summary = (analysis_result.get("executive_summary", "Analysis complete.") or "")[:200]
    _add_textbox(section_dir, "02", f"💡 {summary}", 0, 60, 1280, 40, fontSize=12, color="#666666")

    slicer_x = 0
    for i, dim in enumerate(cat_cols[:3]):
        _add_slicer(section_dir, f"10{i}", table_name, dim, slicer_x, 110, 200, 100)
        slicer_x += 220

    _add_bar_chart(section_dir, "20", table_name, cat_col, y_col,
                   f"Total {y_col} by {cat_col}", 0, 220, 600, 280)
    if date_col:
        _add_line_chart(section_dir, "21", table_name, date_col, y_col,
                        f"{y_col} over time", 620, 220, 660, 280)
    else:
        _add_donut_chart(section_dir, "21", table_name, cat_col, y_col,
                         f"Distribution of {y_col}", 620, 220, 660, 280)


def _build_page_details(sections_dir, section_id, table_name, columns):
    section_dir = os.path.join(sections_dir, section_id)
    os.makedirs(section_dir, exist_ok=True)
    os.makedirs(os.path.join(section_dir, "visualContainers"), exist_ok=True)

    with open(os.path.join(section_dir, "section.json"), "w") as f:
        json.dump({"name": "Details", "displayName": "Details", "ordinal": 1}, f, indent=2)
    with open(os.path.join(section_dir, "config.json"), "w") as f:
        f.write("{}")
    with open(os.path.join(section_dir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f, indent=2)

    _add_textbox(section_dir, "01", "📋 Details — All Records", 0, 0, 1280, 50, fontSize=18, bold=True)
    _add_table_visual(section_dir, "10", table_name, columns, 0, 60, 1280, 660)


def _hash5(s):
    return hashlib.md5(s.encode()).hexdigest()[:5]


def _add_textbox(section_dir, vid, text, x, y, w, h, fontSize=12, bold=False, color="#000000"):
    vdir = os.path.join(section_dir, "visualContainers", f"{vid}_textbox_{_hash5(text)}")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "config.json"), "w") as f:
        json.dump({
            "name": f"textbox_{vid}",
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
            "visualType": "textbox",
            "objects": {
                "general": [{
                    "properties": {
                        "text": {"expr": {"Literal": f"'{text}'"}},
                        "fontSize": {"expr": {"Literal": f"{fontSize}"}},
                        "fontColor": {"expr": {"Literal": f"'{color}'"}},
                        "bold": {"expr": {"Literal": str(bool(bold)).lower()}}
                    }
                }]
            }
        }, f, indent=2)
    with open(os.path.join(vdir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f)
    with open(os.path.join(vdir, "visualContainer.json"), "w") as f:
        json.dump({"name": f"textbox_{vid}", "displayName": "Textbox"}, f)


def _add_slicer(section_dir, vid, table_name, column, x, y, w, h):
    vdir = os.path.join(section_dir, "visualContainers", f"{vid}_slicer_{_hash5(column)}")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "config.json"), "w") as f:
        json.dump({
            "name": f"slicer_{column}",
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
            "visualType": "slicer",
            "objects": {
                "fields": [{
                    "properties": {
                        "field": {
                            "expr": {
                                "Column": {
                                    "Expression": {"SourceRef": {"Entity": table_name}},
                                    "Property": column
                                }
                            }
                        }
                    }
                }]
            }
        }, f, indent=2)
    with open(os.path.join(vdir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f)
    with open(os.path.join(vdir, "visualContainer.json"), "w") as f:
        json.dump({"name": f"slicer_{column}", "displayName": f"Slicer: {column}"}, f)


def _add_bar_chart(section_dir, vid, table_name, cat_col, val_col, title, x, y, w, h):
    vdir = os.path.join(section_dir, "visualContainers", f"{vid}_bar_{_hash5(cat_col)}")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "config.json"), "w") as f:
        json.dump({
            "name": f"bar_{cat_col}_{val_col}",
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
            "visualType": "clusteredColumnChart",
            "queryConstraints": {"maxRecords": 1000},
            "objects": {"general": [{"properties": {"title": {"expr": {"Literal": f"'{title}'"}}}}]},
            "columnProperties": {
                "Category": [{"properties": {"queryName": cat_col}}],
                "Y": [{"properties": {"queryName": val_col}}]
            }
        }, f, indent=2)
    with open(os.path.join(vdir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f)
    with open(os.path.join(vdir, "visualContainer.json"), "w") as f:
        json.dump({"name": f"bar_{cat_col}_{val_col}", "displayName": title}, f)


def _add_line_chart(section_dir, vid, table_name, date_col, val_col, title, x, y, w, h):
    vdir = os.path.join(section_dir, "visualContainers", f"{vid}_line_{_hash5(date_col)}")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "config.json"), "w") as f:
        json.dump({
            "name": f"line_{date_col}_{val_col}",
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
            "visualType": "lineChart",
            "objects": {"general": [{"properties": {"title": {"expr": {"Literal": f"'{title}'"}}}}]},
            "columnProperties": {
                "Category": [{"properties": {"queryName": date_col}}],
                "Y": [{"properties": {"queryName": val_col}}]
            }
        }, f, indent=2)
    with open(os.path.join(vdir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f)
    with open(os.path.join(vdir, "visualContainer.json"), "w") as f:
        json.dump({"name": f"line_{date_col}_{val_col}", "displayName": title}, f)


def _add_donut_chart(section_dir, vid, table_name, cat_col, val_col, title, x, y, w, h):
    vdir = os.path.join(section_dir, "visualContainers", f"{vid}_donut_{_hash5(cat_col)}")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "config.json"), "w") as f:
        json.dump({
            "name": f"donut_{cat_col}_{val_col}",
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
            "visualType": "donutChart",
            "objects": {"general": [{"properties": {"title": {"expr": {"Literal": f"'{title}'"}}}}]},
            "columnProperties": {
                "Category": [{"properties": {"queryName": cat_col}}],
                "Y": [{"properties": {"queryName": val_col}}]
            }
        }, f, indent=2)
    with open(os.path.join(vdir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f)
    with open(os.path.join(vdir, "visualContainer.json"), "w") as f:
        json.dump({"name": f"donut_{cat_col}_{val_col}", "displayName": title}, f)


def _add_table_visual(section_dir, vid, table_name, columns, x, y, w, h):
    vdir = os.path.join(section_dir, "visualContainers", f"{vid}_table")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "config.json"), "w") as f:
        col_props = {c: [{"properties": {"queryName": c}}] for c in columns}
        json.dump({
            "name": f"table_{table_name}",
            "layouts": [{"id": 0, "position": {"x": x, "y": y, "width": w, "height": h}}],
            "visualType": "tableEx",
            "objects": {"general": [{"properties": {"title": {"expr": {"Literal": f"'{table_name}'"}}}}]},
            "columnProperties": col_props
        }, f, indent=2)
    with open(os.path.join(vdir, "filters.json"), "w") as f:
        json.dump({"version": "1.0", "filters": []}, f)
    with open(os.path.join(vdir, "visualContainer.json"), "w") as f:
        json.dump({"name": f"table_{table_name}", "displayName": f"Table: {table_name}"}, f)


def _write_linguistic_schema(path, table_name, columns):
    with open(path, "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
        f.write('<linguisticSchema version="1.0">\n')
        f.write('  <categories>\n')
        f.write(f'    <category name="Table" value="{table_name}"/>\n')
        f.write('  </categories>\n')
        f.write('  <tables>\n')
        f.write(f'    <table name="{table_name}">\n')
        f.write('      <columns>\n')
        for col in columns:
            f.write(f'        <column name="{col}"/>\n')
        f.write('      </columns>\n')
        f.write('    </table>\n')
        f.write('  </tables>\n')
        f.write('</linguisticSchema>\n')


if __name__ == "__main__":
    print("pbix_real_export loaded.")
    print(f"pbi-tools: {PBI_TOOLS_EXE} ({'OK' if os.path.exists(PBI_TOOLS_EXE) else 'MISSING'})")
