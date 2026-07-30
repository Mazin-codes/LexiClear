from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

def generate(prompt):
    print("Using Gemini model: gemini-3.5-flash")
    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    

    return response.text