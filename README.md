# Example code

```python
from typing import Optional

from chatgpt import ChatGPT, Function, FunctionParameterProperties

def get_current_weather(city: Optional[str] = None, state: Optional[str] = None) -> str:
    """
    :param city: The city, e.g. San Francisco
    :param country: The state, e.g. CA
    """
    assert city is not None and state is not None, "Please provide a city and state."
    return "22"


city_param = FunctionParameterProperties(
    name="city", type="string", description="The city, e.g. San Francisco", required=True
)
state_param = FunctionParameterProperties(name="state", type="string", description="The state, e.g. CA", required=True)


llm = ChatGPT(
    model="gpt-3.5-turbo-0613",
    functions=[
        Function(
            name="get_current_weather",
            description="Get the current weather in a given location.",
            parameters=[city_param, state_param],
            func=get_current_weather,
        )
    ],
)

```
