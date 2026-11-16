from openai import OpenAI
from dotenv import load_dotenv
import os
load_dotenv()
# Point the client to your local machine's Ollama port
client = OpenAI(
    base_url="https://api.ollama.com/v1/chat/completions" ,
    api_key=os.getenv("OLLAMA_API_KEY")
)

def chat_via_openai_style():
    completion = client.chat.completions.create(
        model="llama3.1:8b",
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "Write a 1-line python trick."}
        ],
        temperature=0.3
    )

    print("\n--- Response ---")
    print(completion.choices[0].message.content)

if __name__ == "__main__":
    chat_via_openai_style()