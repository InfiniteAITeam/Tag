"""
OpenAI LLM client for AI-powered operations.
"""

import os
import json
from typing import Optional, Dict, Any, List
from ..exceptions import LLMError, ConfigurationError
from ..config.settings import get_config
from ..utils.logger import get_logger
from ..utils.constants import DEFAULT_LLM_MODEL, LLM_TEMPERATURE

logger = get_logger(__name__)


class OpenAIClient:
    """Client for OpenAI API interactions."""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """
        Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key (uses config if None)
            model: Model name (uses config default if None)
        
        Raises:
            ConfigurationError: If API key is not available
        """
        config = get_config()
        
        self.api_key = api_key or config.openai_api_key
        self.model = model or config.llm_model
        
        if not self.api_key:
            raise ConfigurationError("OpenAI API key not configured")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ConfigurationError("openai package not installed")
        except Exception as e:
            raise ConfigurationError(f"Failed to initialize OpenAI client: {e}")
    
    def call_chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = LLM_TEMPERATURE,
        max_tokens: Optional[int] = None,
        timeout: int = 60
    ) -> str:
        """
        Call OpenAI chat completion API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
            timeout: Request timeout in seconds
        
        Returns:
            Response content string
        
        Raises:
            LLMError: If API call fails
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            raise LLMError(f"OpenAI API call failed: {e}")
    
    def extract_json(self, response_text: str) -> Dict[str, Any]:
        """
        Extract JSON from LLM response.
        
        Args:
            response_text: LLM response text
        
        Returns:
            Parsed JSON as dictionary
        
        Raises:
            LLMError: If JSON cannot be extracted
        """
        # Try direct JSON parsing first
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from code fence
        if "```" in response_text:
            start = response_text.find("```")
            end = response_text.find("```", start + 3)
            if end > start:
                code = response_text[start + 3:end]
                # Remove language specifier if present
                if "\n" in code:
                    code = code.split("\n", 1)[1]
                try:
                    return json.loads(code.strip())
                except json.JSONDecodeError:
                    pass
        
        # Try finding JSON object by braces
        start = response_text.find("{")
        if start != -1:
            depth = 0
            for i in range(start, len(response_text)):
                if response_text[i] == "{":
                    depth += 1
                elif response_text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(response_text[start:i+1])
                        except json.JSONDecodeError:
                            pass
        
        raise LLMError(f"Could not extract JSON from response:\n{response_text[:200]}")
    
    def explain_mapping(
        self,
        spec_item: Dict[str, Any],
        code_location: Dict[str, Any],
        snippet: str
    ) -> Dict[str, Any]:
        """
        Use LLM to explain a KPI to code mapping.
        
        Args:
            spec_item: Specification item from TechSpec
            code_location: Matched code location
            snippet: Code snippet around the match
        
        Returns:
            Dictionary with explanation and suggestions
        """
        system_prompt = (
            "You are a senior analytics implementation engineer. "
            "Analyze a KPI requirement and its matched code location. "
            "Return ONLY a JSON object with fields: "
            "kpi, why_location, suggested_event_name, suggested_params, "
            "implementation_note, risks, code (dict with imports/jsx_attrs/hook)"
        )
        
        user_content = (
            f"KPI: {spec_item.get('description')}\n"
            f"Action: {spec_item.get('action')}\n"
            f"Location: {code_location.get('file')}:{code_location.get('line')}\n"
            f"Snippet:\n{snippet}"
        )
        
        try:
            response = self.call_chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ])
            
            return self.extract_json(response)
        except Exception as e:
            logger.warning(f"LLM mapping explanation failed: {e}")
            return {
                "kpi": spec_item.get("description"),
                "why_location": "Matched by code analysis",
                "suggested_event_name": spec_item.get("adobe_value") or "custom_event",
                "suggested_params": {},
                "implementation_note": "Manual review recommended",
                "risks": [],
                "code": {}
            }
    
    def generate_tracking_code(
        self,
        action: str,
        event_name: str,
        params: Dict[str, Any],
        code_snippet: str
    ) -> Dict[str, str]:
        """
        Use LLM to generate tracking code.
        
        Args:
            action: Action type (click, view, etc.)
            event_name: Event name for tracking
            params: Event parameters
            code_snippet: Code snippet to modify
        
        Returns:
            Dictionary with code sections (imports, jsx_attrs, hook, etc.)
        """
        system_prompt = (
            "You are a React/JavaScript code generation expert. "
            "Generate tracking code for Adobe Analytics. "
            "Return ONLY a JSON object with: imports, jsx_attrs, handler_wrap, hook"
        )
        
        user_content = (
            f"Action: {action}\n"
            f"Event: {event_name}\n"
            f"Params: {json.dumps(params)}\n"
            f"Code:\n{code_snippet}"
        )
        
        try:
            response = self.call_chat([
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ])
            
            return self.extract_json(response)
        except Exception as e:
            logger.warning(f"LLM code generation failed: {e}")
            return {}
