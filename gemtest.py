from google import genai

client = genai.Client(api_key="AIzaSyDhcu5HPI8EM-MswPGU7hTIX34WevFPl98")

content = input("Ask away: ")

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=content,
)

print(response.text)