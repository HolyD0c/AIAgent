from google import genai
from google.genai import types
import PIL.Image

client = genai.Client(api_key="AIzaSyDhcu5HPI8EM-MswPGU7hTIX34WevFPl98")

image = PIL.Image.open('images/image.png')
content = input("Ask away: ")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=[content, image],
)

print(response.text)