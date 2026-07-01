import requests

API_URL = "https://api.scrapegraphai.com/v1/agentic-scrapper"
API_KEY = "sgai-a7a77468-c9e4-4d5d-a7d2-4dd8020412f8"

# Reduced steps: 4 instead of 16 (merge related actions, drop redundant waits)
steps = [
    "In \"Año\" enter 2024. In \"Modelo\" type \"HR-V TOURING CVT 4CIL 2.0L\", select the first suggestion, click \"Continuar\" and wait for the next page.",
    "Select \"Hombre\". Fill: birthdate 09/04/1997, name Oswaldo, zip 11000, a random @gmail.com email, and a 10-digit phone starting with 55.",
    "Click \"Cotizar\" and wait until the results page is fully loaded.",
    "Extract all insurance companies and their \"Pago Anual\" price. Return JSON or CSV with: brand, version, model, zip code, birthdate, gender, and each company name with its price.",
]

payload = {
    "website_url": "https://www.autocompara.com/",
    "user_prompt": "Instructions...",
    "actions": steps,
}

response = requests.post(
    API_URL,
    headers={
        "Content-Type": "application/json",
        "SGAI-APIKEY": API_KEY,
    },
    json=payload,
)

response.raise_for_status()
print("Result:", response.json())
