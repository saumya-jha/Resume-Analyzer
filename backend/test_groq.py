from app.services.groq_client import client, MODEL

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {
            "role": "user",
            "content": "What is Python? Explain in one sentence."
        }
    ],
    temperature=0
)

print(response.choices[0].message.content)