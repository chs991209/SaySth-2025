from autogen_ext.models.openai import OpenAIChatCompletionClient
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

model_client00 = OpenAIChatCompletionClient(
    model="gpt-4.1-nano", api_key=API_KEY, extra_create_args={"temperature": 0.0}
)
model_client01 = OpenAIChatCompletionClient(
    model="gpt-4.1-nano", api_key=API_KEY, extra_create_args={"temperature": 0.1}
)
model_client02 = OpenAIChatCompletionClient(
    model="gpt-4.1-nano", api_key=API_KEY, extra_create_args={"temperature": 0.2}
)
model_client03 = OpenAIChatCompletionClient(
    model="gpt-4.1-nano", api_key=API_KEY, extra_create_args={"temperature": 0.3}
)
model_client04 = OpenAIChatCompletionClient(
    model="gpt-4.1-nano", api_key=API_KEY, extra_create_args={"temperature": 0.4}
)
