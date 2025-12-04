import os, base64, json
from dotenv import load_dotenv
from .rules_loader import load_rules
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
DEFAULT_VAR = os.getenv("DEFAULT_ADOBE_VARIABLE", "eVar27")

def encode_image(path:str)->str:
    with open(path, "rb") as f:
        import base64
        return base64.b64encode(f.read()).decode("utf-8")

def map_to_spec(screenshot_path:str, acceptance_text:str, use_csv_output:bool=True):
    """
    Map acceptance criteria and screenshots to tech spec using Gemini API.
    
    Args:
        screenshot_path: Path to the Figma screenshot
        acceptance_text: Acceptance criteria text
        use_csv_output: If True, includes DataLayer, mandatory/optional fields for CSV export
    
    Returns:
        List of dicts with tech spec rows
    """
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is missing in .env")
    
    # Configure Gemini API
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(GEMINI_MODEL)
    
    system = open("techSpecAgent/prompts/mapper_system.md","r",encoding="utf-8").read()
    rules = load_rules()
    # Ensure variable default from env if not provided in rules
    rules.setdefault("variable", DEFAULT_VAR)

    # Read image and encode it
    with open(screenshot_path, "rb") as img_file:
        image_data = img_file.read()
    
    img_b64 = base64.b64encode(image_data).decode("utf-8")
    
    # Prepare combined text content
    combined_text = f"""{system}

AC (Acceptance Criteria):
{acceptance_text}

RULES (JSON):
{json.dumps(rules, indent=2)}"""
    
    try:
        # Call Gemini API with vision capability
        response = model.generate_content(
            [combined_text,
             {"mime_type": "image/png", "data": img_b64}],
            stream=False,
            generation_config={"temperature": 0.2, "top_p": 1.0}
        )
        content_response = response.text.strip()
    except Exception as e:
        raise RuntimeError(f"Gemini API call failed: {e}")
    
    try:
        data = json.loads(content_response)
        assert isinstance(data, list)
    except Exception as e:
        data = [{
            "kpi_requirement":"LLM_PARSE_ERROR",
            "datalayer_property": None,
            "adobe_variables": rules.get("variable", DEFAULT_VAR),
            "adobe_values": content_response[:2000],
            "mandatory_optional": "Optional",
            "business_context": "Error parsing LLM response"
        }]
    
    # Sanitize defaults
    for row in data:
        row.setdefault("adobe_variables", rules.get("variable", DEFAULT_VAR))
        row.setdefault("datalayer_property", None)
        row.setdefault("mandatory_optional", "Optional")
        row.setdefault("business_context", "")
        row.setdefault("values", "")  # Add empty values column for mapped rows
    
    # Add constant DataLayer values at the beginning
    constant_datalayer = rules.get("constant_datalayer", {})
    if constant_datalayer:
        constant_rows = []
        for datalayer_prop, value in constant_datalayer.items():
            # Get the eVar mapping for this DataLayer property
            evar_mappings = rules.get("bpk_evar_mappings", {})
            evar = evar_mappings.get(datalayer_prop, rules.get("variable", DEFAULT_VAR))
            
            constant_rows.append({
                "kpi_requirement": f"Constant DataLayer: {datalayer_prop}",
                "datalayer_property": datalayer_prop,
                "adobe_variables": evar,
                "adobe_values": "",  # Empty for constant rows
                "values": value,  # Constant value goes here
                "mandatory_optional": "Mandatory",
                "business_context": "Constant value for DataLayer initialization"
            })
        
        # Insert constant rows at the beginning
        data = constant_rows + data
    
    return data
