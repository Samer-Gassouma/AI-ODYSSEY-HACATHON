import json
import google.generativeai as genai
import logging
from typing import Optional, Dict, Any

class DataCleaner:
    def __init__(self, api_key: str):
        """Initialize the DataCleaner with Gemini API key."""
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel("gemini-1.5-pro-latest")
        except Exception as e:
            logging.error(f"Failed to initialize Gemini AI: {e}")
            self.model = None

    def _create_prompt(self, raw_text: str) -> str:
        """Create the cleaning prompt for the AI model."""
        return f"""
You are an AI assistant specializing in structuring messy web scraped text into organized ESG-focused JSON format.

**Task:**  
1. Extract cleaned text from raw input.  
2. Categorize information into ESG sections.  
3. Structure in valid JSON format.

**Required JSON Format:**
{{
  "clean_text": "<cleaned text>",
  "environmental": ["env related sentences"],
  "social": ["social related sentences"],
  "governance": ["governance related sentences"]
}}

**Now process this text:**
{raw_text}
"""

    def structure_scraped_data(self, raw_text: str) -> Optional[Dict[str, Any]]:
        """Clean and structure the raw scraped text."""
        if not self.model or not raw_text:
            return None

        try:
            response = self.model.generate_content(self._create_prompt(raw_text))
            cleaned_json_str = response.text.strip()

            if cleaned_json_str.startswith("```json"):
                cleaned_json_str = cleaned_json_str[7:-3]  

            return json.loads(cleaned_json_str)

        except Exception as e:
            logging.error(f"Data Cleaning Failed: {e}")
            return None
