from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()

def extract(condition: str = "") -> dict:
  client = genai.Client(
      vertexai=True,
      project = os.environ.get("PROJECT"),
      location="global",
  )

  si_text1 = """You are a focused symptom extractor. A user will describe how they feel using natural language. Your task is to:

1. Identify each distinct symptom they mention.
2. If the cause or context (e.g., "due to gas", "from stress", "because of period") is clear, include it.
3. Return ONLY a JSON object with one key, "symptoms", whose value is a dictionary. Each key is a symptom, and its value is the reason/context (or "" if unknown).

Example:
Input: "I have a stomach ache from gas and nausea due to my period."
Output:
{
  "symptoms": {
    "stomach ache": "gas",
    "nausea": "menstrual cycle"
  }
}
Do not output anything except the JSON object.
"""

  contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=condition)]
        )
    ]

  generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=1,
        max_output_tokens=8192,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        response_mime_type="application/json",
        response_schema={
            "type": "OBJECT",
            "properties": {
                "symptoms": {
                    "type": "OBJECT",
                    "description": "Maps each symptom to its cause/context string",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["symptoms"],
            "additionalProperties": False
        },
        system_instruction=[types.Part.from_text(text=si_text1)],
    )

  response = client.models.generate_content(
        model="gemini-2.0-flash-lite-001",
        contents=contents,
        config=generate_content_config
    )

  return json.loads(response.text)