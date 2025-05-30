from google import genai
from google.genai import types
import json
from dotenv import load_dotenv

load_dotenv()

def getRecipe(commonName, scientificName, edibleUses):
  client = genai.Client(
      vertexai=True,
      project="gen-lang-client-0966496051",
      location="global",
  )

  si_text1 = """You are a recipe‐creation assistant. You will be given two variables:

• scientific_name: a plant’s scientific name (string)
• common_name: The plant's common names it is known for (string)
• edible_uses: a description of how its parts are eaten or cooked (string)

Your job is to craft a single recipe that showcases this plant. 
**Output only** the following JSON object—nothing else:

{
 \"recipeName\": \"string\",
 \"ingredients\": [\"string\", ...],
 \"instructions\": \"string\"
}

Do not include any additional keys, explanations, or markdown. Use the information in scientific_name and edible_uses to invent a creative recipe.

#### Example

Input: 
scientific_name: \"Zingiber officinale\"
common_name: \"Ginger\"
edible_uses: \"The rhizomes are widely used as a flavouring, added to cakes, curries, chutneys, stir-fries, candies, and beverages like ginger beer.\"

Expected output:
```json
{
 \"recipeName\": \"Spiced Ginger Honey Glaze\",
 \"ingredients\": [
   \"2 tablespoons finely grated fresh ginger\",
   \"1/4 cup honey\",
   \"1 tablespoon soy sauce\",
   \"1 teaspoon rice vinegar\",
   \"Pinch of red pepper flakes\"
 ],
 \"instructions\": \"In a small saucepan, combine grated ginger, honey, soy sauce, rice vinegar, and red pepper flakes. Bring to a gentle simmer over medium heat and cook for 3–4 minutes, stirring occasionally. Remove from heat and let cool slightly. Brush over roasted vegetables, chicken, or tofu just before serving.\"You are a recipe‐creation assistant. You will be given two variables:

• scientific_name: a plant’s scientific name (string)
• common_name: The plant's common names it is known for (string)
• edible_uses: a description of how its parts are eaten or cooked (string)

Your job is to craft a single recipe that showcases this plant. 
**Output only** the following JSON object—nothing else:

{
 \"recipeName\": \"string\",
 \"ingredients\": [\"string\", ...],
 \"instructions\": \"string\"
}

Do not include any additional keys, explanations, or markdown. Use the information in scientific_name and edible_uses to invent a creative recipe.

#### Example

Input: 
scientific_name: \"Zingiber officinale\"
common_name: \"Ginger\"
edible_uses: \"The rhizomes are widely used as a flavouring, added to cakes, curries, chutneys, stir-fries, candies, and beverages like ginger beer.\"

Expected output:
```json
{
 \"recipeName\": \"Spiced Ginger Honey Glaze\",
 \"ingredients\": [
   \"2 tablespoons finely grated fresh ginger\",
   \"1/4 cup honey\",
   \"1 tablespoon soy sauce\",
   \"1 teaspoon rice vinegar\",
   \"Pinch of red pepper flakes\"
 ],
 \"instructions\": \"In a small saucepan, combine grated ginger, honey, soy sauce, rice vinegar, and red pepper flakes. Bring to a gentle simmer over medium heat and cook for 3–4 minutes, stirring occasionally. Remove from heat and let cool slightly. Brush over roasted vegetables, chicken, or tofu just before serving.\"You are a recipe‐creation assistant. You will be given two variables:

• scientific_name: a plant’s scientific name (string)
• common_name: The plant's common names it is known for (string)
• edible_uses: a description of how its parts are eaten or cooked (string)

Your job is to craft a single recipe that showcases this plant. 
**Output only** the following JSON object—nothing else:

{
 \"recipeName\": \"string\",
 \"ingredients\": [\"string\", ...],
 \"instructions\": \"string\"
}

Do not include any additional keys, explanations, or markdown. Use the information in scientific_name and edible_uses to invent a creative recipe.

#### Example

Input: 
scientific_name: \"Zingiber officinale\"
common_name: \"Ginger\"
edible_uses: \"The rhizomes are widely used as a flavouring, added to cakes, curries, chutneys, stir-fries, candies, and beverages like ginger beer.\"

Expected output:
```json
{
 \"recipeName\": \"Spiced Ginger Honey Glaze\",
 \"ingredients\": [
   \"2 tablespoons finely grated fresh ginger\",
   \"1/4 cup honey\",
   \"1 tablespoon soy sauce\",
   \"1 teaspoon rice vinegar\",
   \"Pinch of red pepper flakes\"
 ],
 \"instructions\": \"In a small saucepan, combine grated ginger, honey, soy sauce, rice vinegar, and red pepper flakes. Bring to a gentle simmer over medium heat and cook for 3–4 minutes, stirring occasionally. Remove from heat and let cool slightly. Brush over roasted vegetables, chicken, or tofu just before serving.\"You are a recipe‐creation assistant. You will be given two variables:

• scientific_name: a plant’s scientific name (string)
• common_name: The plant's common names it is known for (string)
• edible_uses: a description of how its parts are eaten or cooked (string)

Your job is to craft a single recipe that showcases this plant. 
**Output only** the following JSON object—nothing else:

{
 \"recipeName\": \"string\",
 \"ingredients\": [\"string\", ...],
 \"instructions\": \"string\"
}

Do not include any additional keys, explanations, or markdown. Use the information in scientific_name and edible_uses to invent a creative recipe.

#### Example

Input: 
scientific_name: \"Zingiber officinale\"
common_name: \"Ginger\"
edible_uses: \"The rhizomes are widely used as a flavouring, added to cakes, curries, chutneys, stir-fries, candies, and beverages like ginger beer.\"

Expected output:
```json
{
 \"recipeName\": \"Spiced Ginger Honey Glaze\",
 \"ingredients\": [
   \"2 tablespoons finely grated fresh ginger\",
   \"1/4 cup honey\",
   \"1 tablespoon soy sauce\",
   \"1 teaspoon rice vinegar\",
   \"Pinch of red pepper flakes\"
 ],
 \"instructions\": \"In a small saucepan, combine grated ginger, honey, soy sauce, rice vinegar, and red pepper flakes. Bring to a gentle simmer over medium heat and cook for 3–4 minutes, stirring occasionally. Remove from heat and let cool slightly. Brush over roasted vegetables, chicken, or tofu just before serving.\""""

  model = "gemini-2.5-flash-preview-05-20"
  contents = [
    types.Content(
      role="user",
      parts=[
        types.Part.from_text(text=f"""common_name:{commonName}, scietific_name:{scientificName}, edible_uses:{edibleUses}""")
      ]
    )
  ]

  generate_content_config = types.GenerateContentConfig(
    temperature = 1,
    top_p = 1,
    seed = 0,
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
    response_schema = {"type":"OBJECT","properties":{"output":{"type":"OBJECT","properties":{"recipeName":{"type":"STRING"},"ingredients":{"type":"ARRAY","items":{"type":"STRING"}},"instructions":{"type":"STRING"}},"required":["recipeName","ingredients","instructions"],"additionalProperties":False}},"required":["output"],"additionalProperties":False},
    system_instruction=[types.Part.from_text(text=si_text1)],
    thinking_config=types.ThinkingConfig(
      thinking_budget=0,
    ),
  )

  response = client.models.generate_content(
    model=model,
    contents=contents,
    config=generate_content_config
  )

  return json.loads(response.text)