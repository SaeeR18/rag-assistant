import os
from dotenv import load_dotenv
from google import genai

# 1. Read the key from the .env file
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise SystemExit("No key found. Check your .env file.")

# 2. Connect to Gemini
client = genai.Client(api_key=api_key)

# 3. Show which models this key can use
print("Models available to your key:")
for model in client.models.list():
    if "generateContent" in (model.supported_actions or []):
        print("  ", model.name)

# 4. Ask one question
MODEL = "gemini-3.5-flash-lite"
print("\nAsking", MODEL, "...")
response = client.models.generate_content(
    model=MODEL,
    contents="In one sentence, what is RAG in AI?",
)
print("Answer:", response.text)