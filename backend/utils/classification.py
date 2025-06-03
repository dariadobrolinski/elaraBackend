from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

load_dotenv()

def classifyCondition(symptoms_dict: dict[str, str]) -> dict:
  client = genai.Client(
      vertexai=True,
      project = os.environ.get("PROJECT"),
      location="global",
  )

  symptoms_with_context = []
  for symptom, context in symptoms_dict.items():
        if context and context.strip():
            symptoms_with_context.append(f"{symptom} due to {context}")
        else:
            symptoms_with_context.append(symptom)

    # 2. Wrap the list in the expected JSON shape: { "inputs": [ … ] }
  user_payload = {"inputs": symptoms_with_context}
  user_payload_text = json.dumps(user_payload)

    # 3. System prompt remains the same dictionary of medical uses
  si_text1 = """You are a highly accurate medical-use classification assistant. You have access to the following dictionary of botanical medical uses and their descriptions:

{
 "Abortifacient": "Causes an abortion.",
 "Acrid": "Causes heat and irritation when applied to the skin.",
 "Adaptogen": "Helps the body 'rise' to normal stress situations, thus preventing the many chronic degenerative diseases.",
 "Alterative": "Causes a gradual beneficial change in the body, usually through improved nutrition and elimination, without having any marked specific action.",
 "Anaesthetic": "Numbs the feeling in a local or general area of the body.",
 "Analgesic": "Relieves pain. Included under Anodyne.",
 "Anaphrodisiac": "Reduces sexual desire.",
 "Anodyne": "Relieves pain.",
 "Antacid": "Counters excess acidity in the stomach.",
 "Anthelmintic": "Expels parasites from the gut.",
 "Antiaphonic": "Restores the voice.",
 "Antiarthritic": "Treats arthritis.",
 "Antiasthmatic": "Treats asthma.",
 "Antibilious": "Treats nausea.",
 "Antibiotic": "See antiseptic.",
 "Antibacterial": "Kills bacteria.",
 "Anticholesterolemic": "Prevents the build up of cholesterol.",
 "Anticoagulant": "Removes blood clots.",
 "Antidandruff": "Treats dandruff.",
 "Antidermatosic": "Prevents or cures skin complaints.",
 "Antidote": "Counters poisoning.",
 "Antiecchymotic": "???",
 "Antiemetic": "Prevents vomiting.",
 "Antifungal": "Treats various fungal problems such as Candida.",
 "Antihaemorrhoidal": "Treats haemorrhoids (piles). This would probably be best added to another heading.",
 "Antihalitosis": "Treats bad breath.",
 "Antihydrotic": "Reduces perspiration.",
 "Antiinflammatory": "Reduces inflammation of joints, injuries etc.",
 "Antiperiodic": "Counteracts recurring illnesses such as malaria.",
 "Antiphlogistic": "Reduces inflammation.",
 "Antipruritic": "Treats itching of the skin.",
 "Antipyretic": "Treats fevers. See Febrifuge.",
 "Antirheumatic": "Treats rheumatism.",
 "Antiscorbutic": "A plant rich in vitamin C that is used to counteract scurvy.",
 "Antiscrophulatic": "Counteracts scrofula. (TB, especially of the lymph glands)",
 "Antiseptic": "Destroys or arrests the growth of micro-organisms.",
 "Antispasmodic": "Treats muscular spasms and cramps.",
 "Antitumor": "Used in the treatment of cancer. This should probably be included in cytotoxic.",
 "Antitussive": "Treats coughing.",
 "Antivinous": "Treats addiction to alcohol.",
 "Antiviral": "Treats virus diseases.",
 "Aperient": "A mild laxative.",
 "Aphrodisiac": "Increases the sexual appetite.",
 "Appetizer": "Improves the appetite.",
 "Aromatherapy": "Plants whose essential oils are used in Aromatherapy.",
 "Aromatic": "Having an agreeable odour and stimulant qualities.",
 "Astringent": "Reduces the flow of secretions and discharges of blood, mucus, diarrhoea etc.",
 "Bach": "Plants used in the Bach flower remedies.",
 "Balsamic": "A healing and soothing agent.",
 "Bitter": "Increases the appetite and stimulates digestion by acting on the mucous membranes of the mouth. Also increases the flow of bile, stimulates repair of the gut wall lining and regulates the secretion of insulin and glucogen.",
 "Blood purifier": "Purifies the blood.",
 "Blood tonic": "Is this any different to a blood purifier?",
 "Cancer": "Used in the treatment of cancer.",
 "Cardiac": "Used in the treatment of heart problems.",
 "Cardiotonic": "A tonic for the heart.",
 "Carminative": "Reduces flatulence and expels gas from the intestines.",
 "Cathartic": "A strong laxative but less violent than a purgative.",
 "Cholagogue": "Increases the flow of bile and its discharge from the body.",
 "Contraceptive": "Prevents fertilization occurring in females.",
 "Cytostatic": "Slows or controls the growth of tumours.",
 "Cytotoxic": "Destroys body cells. Used in the treatment of diseases such as cancer.",
 "Decongestant": "Removes phlegm and mucous, especially from the respiratory system.",
 "Demulcent": "Soothes irritated tissues, especially the mucous membranes.",
 "Deobstruent": "Clears obstructions from the natural ducts of the body.",
 "Deodorant": "Masks smells. Is this medicinal?",
 "Depurative": "Eliminates toxins and purifies the system, especially the blood.",
 "Detergent": "A cleansing agent, used on wounds etc. It removes dead and diseased matter.",
 "Diaphoretic": "Induces perspiration.",
 "Digestive": "Aids digestion.",
 "Disinfectant": "Used for cleaning wounds.",
 "Diuretic": "Promotes the flow of urine.",
 "Emetic": "Induces vomiting.",
 "Emmenagogue": "Restores the menstrual flow, sometimes by inducing an abortion.",
 "Emollient": "Softens the skin.",
 "Enuresis": "Treats bed wetting.",
 "Errhine": "",
 "Expectorant": "Clears phlegm from the chest by inducing coughing.",
 "Febrifuge": "Reduces fevers.",
 "Foot care": "Plants that are used in various ways to treat foot problems.",
 "Galactofuge": "Stops the flow of milk in a nursing mother.",
 "Galactogogue": "Promotes the flow of milk in a nursing mother.",
 "Haemolytic": "Breaks down red blood corpuscles to separate haemoglobin.",
 "Haemostatic": "Controls internal bleeding.",
 "Hallucinogenic": "Causes the mind to hallucinate.",
 "Hepatic": "Acts on the liver (for better or worse!).",
 "Hydrogogue": "A purgative that causes an abundant watery discharge.",
 "Hypnotic": "Induces sleep.",
 "Hypoglycaemic": "Reduces the levels of sugar in the blood.",
 "Hypotensive": "Reduces high blood pressure.",
 "Infertility": "Used in problems of human fertility.",
 "Irritant": "Causes irritation or abnormal sensitivity in living tissue.",
 "Kidney": "Used in the treatment of kidney diseases.",
 "Laxative": "Stimulates bowel movements in a fairly gentle manner.",
 "Lenitive": "Soothing, palliative.",
 "Lithontripic": "Removes stones.",
 "Miscellany": "Various medicinal actions that need more clarification.",
 "Mouthwash": "Treats problems such as mouth ulcers.",
 "Mydriatic": "Dilates the pupils of the eyes.",
 "Narcotic": "Induces drowsiness and gives an artificial sense of well-being.",
 "Nervine": "Stimulates and calms the nerves.",
 "Nutritive": "A food for convalescents to help restore strength.",
 "Odontalgic": "Treats toothache (temporary measure only) and other problems of the teeth and gums.",
 "Ophthalmic": "Treats eye complaints.",
 "Oxytoxic": "Hastens parturition and stimulates uterine contractions.",
 "Parasiticide": "Treats external parasites such as ringworm.",
 "Pectoral": "Relieves respiratory diseases, a remedy for chest diseases.",
 "Plaster": "Used in the treatment of broken bones.",
 "Poultice": "Used in the treatment of burns etc.",
 "Purgative": "A drastic laxative.",
 "Refrigerant": "Cools the body.",
 "Resolvent": "Breaks down tumors.",
 "Restorative": "Restores consciousness or normal physiological activity.",
 "Rubefacient": "A counter-irritant and external stimulant.",
 "Salve": "Soothes and heals damaged skin.",
 "Sedative": "Gently calms, reducing nervousness, distress and irritation.",
 "Sialagogue": "Stimulates the secretion of saliva.",
 "Skin": "Plants used in miscellaneous treatments for the skin.",
 "Sternutatory": "Promotes sneezing and nasal discharges.",
 "Stimulant": "Excites or quickens activity of the physiological processes. Faster acting than a tonic but differing from a narcotic in that it does not give a false sense of well-being.",
 "Stings": "Used in the treatment of stings and insect bites.",
 "Stomachic": "Aids and improves the action of the stomach.",
 "Styptic": "An astringent that stops bleeding by contracting the blood vessels.",
 "TB": "Plants used in the treatment of tuberculosis.",
 "Tonic": "Improves general health. Slower acting than a stimulant, it brings steady improvement.",
 "Uterine tonic": "See also oxytoxic.",
 "Vasoconstrictor": "Narrows the blood vessels, thereby increasing blood pressure.",
 "Vasodilator": "Widens the blood vessels, thereby reducing blood pressure.",
 "VD": "Used in the treatment of venereal disease.",
 "Vermifuge": "Expels internal parasites.",
 "Vesicant": "A blistering agent.",
 "Vulnerary": "Heals wounds.",
 "Warts": "Used in the treatment of warts, corns etc.",
 "Women's complaints": "A very vague title, it deals with a miscellany of problems peculiar to the female sex."
}
INSTRUCTION:
• The user will send you a JSON object with a single key, "inputs", whose value is an array of symptom strings (already including context).
• Your job is to return ONLY a JSON object with a single key, "outputs", whose value is a dictionary mapping each symptom string exactly to the best matching medical-use classification from the dictionary above.
• Do NOT include descriptions, commentary, or any extra keys—just the JSON.

EXAMPLE:
User sends:
{
  "inputs": ["stomach ache due to gas", "nausea due to pregnancy"]
}
Your response MUST be:
{
  "outputs": {
    "stomach ache due to gas": "Carminative",
    "nausea due to pregnancy": "Antiemetic"
  }
}
"""

  model = "gemini-2.5-flash-preview-05-20"
  contents = [
    types.Content(
      role="user",
      parts=[
         types.Part.from_text(text=user_payload_text)
      ]
    ),
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
    response_schema = {"type":"OBJECT","properties":{"outputs":{"type":"OBJECT","description":"Maps each symptom to the best matching medical-use classification name","additionalProperties":{"type":"string"}}},"required":["outputs"],"additionalProperties":False},
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
