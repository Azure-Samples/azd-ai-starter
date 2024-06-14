from quart import Quart, request
from openai import AzureOpenAI
from dotenv import load_dotenv
import os

load_dotenv()
azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
azure_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

app = Quart(__name__)

@app.route("/api/chat", methods=['POST'])
async def chat():
    # Get the message from the request data
    data = await request.get_json()
    message = data["message"]

    # gets the API Key from environment variable AZURE_OPENAI_API_KEY
    client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
    )

    completion = client.chat.completions.create(
        model=azure_deployment,
        messages=[
            {
                "role": "user",
                "content": message,
            },
        ],
    )

    return completion.choices[0].message.content

if __name__ == "__main__":
    app.run()
