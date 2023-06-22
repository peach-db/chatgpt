import copy
import json
from typing import Any, Dict, List, Optional

import openai
from tenacity import retry, stop_after_attempt, wait_random_exponential


@retry(wait=wait_random_exponential(min=1, max=40), stop=stop_after_attempt(3))
def _chat_completion_request(**kwargs):
    return openai.ChatCompletion.create(**kwargs)


class FunctionParameterProperties:
    """
    Class to represent the properties of a function parameter.

    Attributes:
        name (str): Parameter name.
        type (str): Parameter type.
        description (str): Parameter description.
        _required (bool): Flag to determine if the parameter is required.
    """

    def __init__(self, name: str, type: str, description: str, required: bool) -> None:
        self.name = name
        self.type = type
        self.description = description
        self._required = required

    @property
    def json(self) -> Dict[str, Any]:
        """Generate a dictionary representation of the parameter properties."""
        return {
            "type": self.type,
            "description": self.description,
        }

    @property
    def required(self) -> bool:
        """Return the requirement status of the parameter."""
        return self._required


class FunctionParameters:
    """
    Class to represent a set of parameters for a function.

    Attributes:
        type (str): Type of parameters object (default is "object").
        properties (List[FunctionParameterProperties]): A list of parameter properties.
    """

    def __init__(self, properties: List[FunctionParameterProperties]):
        self.type = "object"
        self.properties = properties

    @property
    def json(self) -> Dict[str, Any]:
        """Generate a dictionary representation of the function parameters."""
        return {
            "type": self.type,
            "properties": {x.name: x.json for x in self.properties},
            "required": [x.name for x in self.properties if x.required],
        }


class Function:
    """
    Class to represent a function.

    Attributes:
        name (str): Function name.
        description (str): Function description.
        parameters (FunctionParameters): Function parameters.
        func (Any): Actual function.
    """

    def __init__(self, name: str, description: str, parameters: List[FunctionParameterProperties], func: Any):
        self.name = name
        self.description = description
        self.parameters = FunctionParameters(parameters)
        self.func = func

    @property
    def json(self) -> Dict[str, Any]:
        """Generate a dictionary representation of the function."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters.json,
        }


def _validate_openai_credentials():
    """
    Utility function to validate OpenAI API credentials.

    Raises:
        ValueError: If OpenAI API key is not set in environment.
    """
    if openai.api_key is None:
        raise ValueError(
            "OpenAI API key not found. Please set the OPENAI_API_KEY environment variable to your API key."
        )


class ChatGPT:
    """
    Class to represent the ChatGPT model.

    Attributes:
        model (str): Model identifier.
        functions (Optional[List[Function]]): A list of function objects.
        messages (Optional[List[Dict[str, Any]]]): A list of chat messages.
        system_prompt (Optional[str]): System prompt message.
        call_fn_on_every_user_message (Optional[str]): Name of the function to call after every user message.
    """

    def __init__(
        self,
        model: str,
        functions: Optional[List[Function]] = None,
        messages: Optional[List[Dict[str, Any]]] = None,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        call_fn_on_every_user_message: Optional[str] = None,
    ):
        _validate_openai_credentials()
        self._initialize_messages(messages, system_prompt)
        self.model = model
        self.functions = functions
        self.temperature = temperature
        self.call_fn_on_every_user_message = call_fn_on_every_user_message

        if self.call_fn_on_every_user_message is not None:
            if self.functions is None:
                raise ValueError("No functions provided.")
            if self.call_fn_on_every_user_message not in [func.name for func in self.functions]:
                raise ValueError(
                    f"Function to call on every user msg ({self.call_fn_on_every_user_message}) not found in provided functions."
                )

    def _initialize_messages(self, messages: Optional[List[Dict[str, Any]]], system_prompt: Optional[str]) -> None:
        """
        Private method to initialize the messages list based on given arguments.

        Args:
            messages (Optional[List[Dict[str, Any]]]): A list of chat messages.
            system_prompt (Optional[str]): System prompt message.

        Raises:
            ValueError: If both messages and system_prompt are provided.
        """
        if messages is None:
            self.messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
        elif system_prompt is None:
            self.messages = messages
        else:
            raise ValueError("Cannot provide both system_prompt and messages.")

    @property
    def json(self) -> Dict[str, Any]:
        """Generate a dictionary representation of the ChatGPT model."""
        gpt_json = {
            "model": self.model,
            "messages": self.messages,
        }

        if self.functions is not None:
            gpt_json["functions"] = [func.json for func in self.functions]

        if self.temperature is not None:
            gpt_json["temperature"] = self.temperature

        return gpt_json

    def __call__(self, user_message: str) -> List[Dict[str, Any]]:
        """Process a user message through the ChatGPT model and return response messages."""
        # TODO: add streaming
        response_messages = self._get_responses_from_openai(user_message)
        return response_messages

    def _get_responses_from_openai(self, user_message: str) -> List[Dict[str, Any]]:
        """Private method to generate responses from the OpenAI ChatCompletion API."""
        user_content = {"role": "user", "content": user_message}

        self.messages.append(user_content)

        response_messages = []
        while True:
            # TODO: below is ugly, refactor.
            call_kwargs = copy.deepcopy(self.json)
            if call_kwargs["messages"][-1]["role"] == "user":
                if self.call_fn_on_every_user_message is not None:
                    call_kwargs["function_call"] = {"name": self.call_fn_on_every_user_message}

            response = _chat_completion_request(**call_kwargs)
            response_message = dict(response.choices[0].message)
            response_messages.append(response_message)
            self.messages.append(response_message)

            if "function_call" not in response_message:
                break

            response_messages.append(self._process_function_call(response_message))

        return response_messages

    def _process_function_call(self, response_message: Dict[str, Any]) -> Dict[str, Any]:
        """Private method to process a function call embedded in a response message."""
        if self.functions is None:
            raise ValueError("No functions provided.")

        fn_name = response_message["function_call"]["name"]
        fn_args = json.loads(response_message["function_call"]["arguments"])
        print(fn_name, fn_args)

        matched_fns = [func for func in self.functions if func.name == fn_name]
        if len(matched_fns) == 0:
            raise ValueError(f"Function {fn_name} not found.")
        elif len(matched_fns) > 1:
            raise ValueError(f"Multiple functions with name {fn_name} found.")
        else:
            fn = matched_fns[0]

        fn_response = fn.func(**fn_args)

        message = {"role": "function", "name": fn_name, "content": str(fn_response)}
        self.messages.append(message)
        return message
