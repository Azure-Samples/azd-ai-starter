import os

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv
from openai import AzureOpenAI
from quart import Quart, request

load_dotenv()
azure_endpoint = os.environ["AZURE_OPENAI_ENDPOINT"]
azure_deployment = os.environ["AZURE_OPENAI_DEPLOYMENT"]

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

app = Quart(__name__)


@app.route("/api/chat", methods=['POST'])
async def chat():
    # Get the message from the request data
    data = await request.get_json()
    message = data["message"]

    # gets the API Version from envrionment variable OPENAI_API_VERSION
    client = AzureOpenAI(
        azure_endpoint=azure_endpoint,
        azure_ad_token_provider=token_provider,
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
