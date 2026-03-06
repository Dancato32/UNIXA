import requests

# Your API key
API_KEY = "4276081c0b484a1a93d924fbcf8c0cb2.7BF2yFemgcVvbjbn"

# Base URL for the LLM API (replace with the actual endpoint if different)
BASE_URL = "https://api.z.ai/v1/llm/generate"

# Example payload
data = {
    "prompt": "Explain the concept of Python decorators in simple terms.",
    "max_tokens": 150,
    "temperature": 0.7
}

# Headers with your API key
headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Make the POST request
response = requests.post(BASE_URL, json=data, headers=headers)

# Check response
if response.status_code == 200:
    result = response.json()
    print("LLM Response:", result)
else:
    print(f"Error {response.status_code}: {response.text}")