import openai
import os
from openai import OpenAI

# openai.api_key = os.getenv("OPENAI_API_KEY")  # You could also directly assign the key if you wish.

# Load the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(
    # This is the default and can be omitted
    # api_key=os.environ.get("OPENAI_API_KEY"),
    api_key = api_key,
)

try: 
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-4o-mini",
    )
     # Debugging step: Print the entire response to check its structure
    print("Full Response:")
    print(chat_completion)
    
    if chat_completion and hasattr(chat_completion, 'choices'):
        response_content = chat_completion.choices[0].message.content
        print(f"ChatGPT Response: {response_content}")
    else:
        print("No response was received.")

except Exception as e:
    print(f"An error occurred: {e}")