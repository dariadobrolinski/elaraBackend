from google import genai
from google.genai import types
import json
from dotenv import load_dotenv

load_dotenv()

def extract(condition: str = 'Cancer'):
  client = genai.Client(
      vertexai=True,
      project="gen-lang-client-0966496051",
      location="global",
  )

  si_text1 = """You are a focused symptom extractor. Whenever you receive user input describing how someone feels, do exactly two things:
1. Identify every symptom phrase in the input.
2. Output **only** a JSON object with a single key, `\"symptoms\"`, whose value is an array of those symptom strings.

⚠️ Do not emit any extra text, commentary, or formatting—just the JSON.

Example:
User: \"I have a headache and feel nauseous…\"
Model ↴
{
 \"symptoms\": [\"headache\", \"nausea\", …]
}"""

  model = "gemini-2.0-flash-lite-001"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text=condition)
      ]
    )
  ]

  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 1,
    max_output_tokens = 8192,
    safety_settings = [types.SafetySetting(
      category="HARM_CATEGORY_HATE_SPEECH",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_DANGEROUS_CONTENT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_SEXUALLY_EXPLICIT",
      threshold="OFF"
    ),types.SafetySetting(
      category="HARM_CATEGORY_HARASSMENT",
      threshold="OFF"
    )],
    response_mime_type = "application/json",
    response_schema = {"type":"OBJECT","properties":{"symptoms":{"type":"ARRAY","items":{"type":"STRING"}}},"required":["symptoms"],"additionalProperties":False},
    system_instruction=[types.Part.from_text(text=si_text1)],
  )

  response = client.models.generate_content(
    model=model,
    contents=contents,
    config=generate_content_config
  )

  return json.loads(response.text)