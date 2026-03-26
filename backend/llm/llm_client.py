import requests, os

API_KEY = os.getenv("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")

def generate_query(q):
    res = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={
            "model": "mistralai/mistral-7b-instruct",
            "messages": [
                {"role": "system", "content": "Convert to Cypher"},
                {"role": "user", "content": q}
            ]
        }
    )
    return res.json()["choices"][0]["message"]["content"]