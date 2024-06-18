import uuid

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from openai import AzureOpenAI
from quart import Quart, g, request
from stateStore import StateStore
from config import Config

token_provider = get_bearer_token_provider(
    DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")

app = Quart(__name__)

config = Config()
state_store = StateStore()


@app.before_request
async def load_history():
    data = await request.get_json()
    messages = data.get('messages', [])
    session_state = data.get('sessionState', None)

    if session_state:
        try:
            history = state_store.read(session_state)
            messages = history + messages
        except ValueError:
            pass
    else:
        session_state = str(uuid.uuid4())

    g.messages = [
        {"role": "system", "content": config.system_prompt}] + messages
    g.session_state = session_state


@app.route("/api/chat", methods=['POST'])
async def chat():
    messages = g.messages
    session_state = g.session_state

    client = AzureOpenAI(
        api_version=config.azure_api_version,
        azure_endpoint=config.azure_endpoint,
        azure_ad_token_provider=token_provider,
    )

    completion = client.chat.completions.create(
        model=config.azure_deployment,
        messages=messages,
        max_tokens=1024
    )
    choice = completion.choices[0]
    responseMessage = {
        "role": choice.message.role,
        "content": choice.message.content
    }

    state_store.save(session_state, messages + [responseMessage])

    return {"messages": responseMessage, "sessionState": session_state}

if __name__ == "__main__":
    app.run()
