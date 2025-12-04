import os, pandas as pd, csv
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "./TechSpecOutputs")

def write_excel(rows:list)->str:
    """Write tech spec to Excel format (legacy format)"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = pd.DataFrame([
        {"KPI Requirement": r.get("kpi_requirement",""),
         "Adobe Variables": r.get("adobe_variables",""),
         "Adobe Values": r.get("adobe_values","")}
        for r in rows
    ])
    out_path = os.path.join(OUTPUT_DIR, "techspec.xlsx")
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Reporting Requirement")
    return out_path

def write_csv(rows:list)->str:
    """Write tech spec to CSV format with DataLayer properties and mandatory/optional status"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_DIR, f"BPK_AI_Tagging_TechSpec_{timestamp}.csv")
    
    with open(out_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = [
            'KPI Requirement',
            'DataLayer Property',
            'Adobe Variables',
            'Adobe Values',
            'Values',
            'Mandatory/Optional',
            'Business Context'
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for row in rows:
            writer.writerow({
                'KPI Requirement': row.get('kpi_requirement', ''),
                'DataLayer Property': row.get('datalayer_property', '') or '',
                'Adobe Variables': row.get('adobe_variables', ''),
                'Adobe Values': row.get('adobe_values', ''),
                'Values': row.get('values', ''),
                'Mandatory/Optional': row.get('mandatory_optional', 'Optional'),
                'Business Context': row.get('business_context', '')
            })
    
    return out_path

def write_excel_with_datalayer(rows:list)->str:
    """Write tech spec to Excel format with DataLayer column"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame([
        {
            "KPI Requirement": r.get("kpi_requirement", ""),
            "DataLayer Property": r.get("datalayer_property", "") or "",
            "Adobe Variables": r.get("adobe_variables", ""),
            "Adobe Values": r.get("adobe_values", ""),
            "Values": r.get("values", ""),
            "Mandatory/Optional": r.get("mandatory_optional", "Optional"),
            "Business Context": r.get("business_context", "")
        }
        for r in rows
    ])
    
    out_path = os.path.join(OUTPUT_DIR, f"BPK_AI_Tagging_TechSpec_{timestamp}.xlsx")
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="Reporting Requirement")
    return out_path
