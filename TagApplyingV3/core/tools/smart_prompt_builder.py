"""
Smart Prompt Builder - Reads Tagging Framework and generates intelligent prompts

This module creates prompts where LLM can:
1. Understand the Tagging framework (what functions are available)
2. Read the target file (what context exists)
3. Decide what imports and calls are needed (not hardcoded)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional


class SmartPromptBuilder:
    """Builds intelligent prompts by reading Tagging framework and target files"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.tagging_framework_path = self.repo_path / "src" / "pages" / "ExpressStore" / "Tagging" / "index.js"
        self.tagging_framework = None
        
    def _read_file(self, file_path: Path) -> Optional[str]:
        """Safely read file content"""
        try:
            if file_path.exists():
                return file_path.read_text(encoding='utf-8')
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
        return None
    
    def get_tagging_framework_context(self) -> str:
        """Read the ACTUAL Tagging framework file and pass it directly to LLM"""
        framework_code = self._read_file(self.tagging_framework_path)
        
        if not framework_code:
            return "# TAGGING FRAMEWORK NOT FOUND"
        
        # Pass the actual framework code to LLM - let LLM analyze it
        framework_context = f"""
# TAGGING FRAMEWORK SOURCE CODE

This is the actual React hook implementation from: `src/pages/ExpressStore/Tagging/index.js`

**READ THIS CODE CAREFULLY** - This is the source of truth.
Understand:
1. What functions are exported
2. What parameters each function accepts
3. How each function is called
4. What each function returns

```javascript
{framework_code}
```

---

## YOUR TASK

You will read the framework code above and:
1. Understand what functions are available
2. Understand what parameters each function expects
3. Understand how to import and use useTagging
4. Apply this understanding to the target file below
"""
        return framework_context
    
    def build_intelligent_prompt(
        self,
        target_file_path: str,
        target_file_content: str,
        instruction: Dict[str, Any],
        anchor_line: int,
        snippet: Optional[str] = None,
    ) -> str:
        """
        Build prompt where LLM reads framework and target file, then decides what to do
        
        NO HARDCODING. LLM learns from the actual framework code.
        
        Args:
            target_file_path: Path to target file
            target_file_content: Full content of target file
            instruction: Dict with action, event, params, etc.
            anchor_line: Line number anchor
            snippet: Optional code snippet context
        
        Returns:
            Complete prompt for LLM
        """
        
        # Get ACTUAL framework code - pass it directly
        framework_context = self.get_tagging_framework_context()
        
        # Extract instruction details - NO defaults, use what's provided
        action = instruction.get("action", "")
        event_type = instruction.get("event", "")
        params = instruction.get("params", {})
        description = instruction.get("description", "")
        
        prompt = f"""{framework_context}

---

## TARGET FILE (the file you need to modify)

**Path**: `{target_file_path}`

```javascript
{target_file_content}
```

---

## TASK REQUIREMENTS

**What to add**:
- Description: {description}
- Action Type: {action}
- Function to call: {event_type}
- Parameters needed: {json.dumps(params, indent=2)}
- Anchor Line: {anchor_line}

---

## INSTRUCTIONS

You are a code transformation assistant. Your job:

1. **READ and ANALYZE the Tagging framework code** (at the top of this prompt)
   - Read the full source code carefully
   - Understand what functions are exported
   - Understand what parameters each function accepts
   - See how useTagging is called
   - DO NOT invent functions

2. **IDENTIFY the function you need to call**: {event_type}
   - Read the framework code to find this function
   - Understand its parameters by reading the function definition
   - These parameters are REQUIRED - you MUST use them

3. **READ the target file** (current React component below)
   - Check if this function is already imported
   - Check if this function is already being called
   - If already present → return UNCHANGED with reason

4. **ADD imports IF MISSING**:
   - Read the framework: how is useTagging imported/exported?
   - Calculate correct relative path based on target file location
   - Add import statement at top if not present
   - useTagging is self-contained - NO other dependencies needed

5. **ADD hook call IF MISSING**:
   - Read the framework: how does useTagging() work?
   - Call it like any React hook and destructure what you need
   - Example: `const {{ {event_type} }} = useTagging();`
   - Place after other hook declarations
   - NO special setup or initialization needed

6. **ADD tracking call with EXACT parameters**:
   - Read the framework code for {event_type} function
   - Use EXACTLY the parameters from "Parameters needed" below
   - Read how the function should be called from framework
   - Determine best place to call (handler, useEffect, catch block, etc.)
   
   **IMPORTANT - useEffect handling for trackPageLoad**:
   - If {event_type} is trackPageLoad: ALWAYS use empty dependency array []
   - Empty dependency array [] means: runs ONLY ONCE on component mount
   - CORRECT: useEffect(() => {{ trackPageLoad(...) }}, [])
   - WRONG: useEffect(() => {{ trackPageLoad(...) }}) without []
   - WRONG: useEffect(() => {{ trackPageLoad(...) }}, [deps])
   - The empty [] is REQUIRED for proper page load tracking behavior

7. **PRESERVE all other code**:
   - Don't modify unrelated parts
   - Don't change formatting or variable names
   - Only add what's needed for this task

8. **Return JSON result**:
   ```json
   {{
     "applied": true/false,
     "reason": "explanation",
     "updated_file": "full file content here or unchanged content"
   }}
   ```

---

## PARAMETER MAPPING

The parameters you MUST use for this task:

"""
        
        # Add detailed parameter mapping
        for param_name, param_value in params.items():
            prompt += f"\n- `{param_name}`: {param_value}"
        
        prompt += f"""

These are the EXACT parameters that must be passed to {event_type}.
Use ONLY these values - do NOT invent or make up values.

---

## KEY RULES

- **Framework is source of truth** - read and understand the actual code
- **Match parameters exactly** - use ONLY what's in the framework
- **NO inventing** - don't create functions or parameters that don't exist
- **Preserve existing code** - don't modify unrelated parts
- **Idempotent** - if already applied, return unchanged
- **Correct paths** - calculate relative import paths based on file location
"""
        
        # Save prompt for debugging
        with open("smart_prompt.txt", 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        return prompt
    

# Example usage
if __name__ == "__main__":
    builder = SmartPromptBuilder(r"C:\Users\ramean3\Desktop\TestCodes\TagApplied_V3\cloned_repo")
    
    # Example instruction
    instruction = {
        "action": "click",
        "event": "trackPageChange",
        "params": {
            "selector": "bill-type-select",
            "message": "Bill type selected",
            "pageName": "Bill type",
            "flow": "BPK Bill type selection"
        }
    }
    
    # Read target file
    target_file = r"C:\Users\ramean3\Desktop\TestCodes\TagApplied_V3\cloned_repo\src\pages\ExpressStore\PayBill\PayBillType\index.js"
    with open(target_file, 'r') as f:
        content = f.read()
    
    with open("target_file_content.txt", 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Build prompt
    prompt = builder.build_intelligent_prompt(
        target_file_path=target_file,
        target_file_content=content,
        instruction=instruction,
        anchor_line=21,
        snippet="handlePaymentSelection click handler"
    )
    
    print("GENERATED PROMPT:")
    print("=" * 80)
    print(prompt)
    print("=" * 80)
