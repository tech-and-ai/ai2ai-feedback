import requests

# Modelfile content
modelfile = """
FROM qwen3:8b
PARAMETER context_length 16384
"""

# Create the model
response = requests.post(
    "http://192.168.0.77:11434/api/create",
    json={
        "name": "qwen3-extended:8b",
        "modelfile": modelfile
    }
)

print(f"Status code: {response.status_code}")
print(response.json())
