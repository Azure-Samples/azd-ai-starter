import os
from dotenv import load_dotenv


class Config:
    def __init__(self):
        load_dotenv()
        self._azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        self._azure_deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT")
        self._azure_api_version = os.environ.get("OPENAI_API_VERSION")
        self._system_prompt = os.environ.get(
            "SYSTEM_PROMPT", "You are a helpful assistant that responds succintly to questions.")

    @property
    def azure_endpoint(self):
        return self._azure_endpoint

    @property
    def azure_deployment(self):
        return self._azure_deployment

    @property
    def azure_api_version(self):
        return self._azure_api_version

    @property
    def system_prompt(self):
        return self._system_prompt
