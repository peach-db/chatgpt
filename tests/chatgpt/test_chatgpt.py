# NOTE: needs to be called from tests/chatgpt!
from chatgpt import ChatGPT, Function, FunctionParameterProperties
from connectors.test_structured import get_cms_data, get_user_data
from joblib import Memory  # type: ignore
from rich import print

document_context = "\n".join(get_cms_data())
# NOTE: we locally cache the user_context as we run GPT-4 for grammar fix and that can take some time.
user_context = Memory(location=".", verbose=0).cache(get_user_data)(max_rows=1)[0]


def update_user_context(context: str = ""):
    # TODO: we might want to append to a list so we don't lose anything?
    global user_context
    user_context = context
    return user_context


system_prompt = (
    "ProGrad helps its users find ways to earn money achieve their life goals. You're a friendly, encouraging bot that helps ProGrad users find ways to earn, "
    + "using information they provide about themselves. If you need information about them (e.g. interests, goals) please ask them. "
    + "Try to learn more about them and their goals. When they say no to something, try to understand why. "
    + "You should only use information and oppurtunities that are provided to you. If you're asked a question that requires you to use your own knowledge, you should say that you don't know and ask the user to email the ProGrad team. "
    + "Get to the point straight away. "
    + f"Here is some information about the user: {user_context}. "
    + f"Here are all the oppurtunities available on ProGrad (only use these and talk about these): \n\n{document_context}"
)


llm = ChatGPT(
    model="gpt-4-0613",
    system_prompt=system_prompt,
    temperature=0,
    call_fn_on_every_user_message="update_user_context",
    functions=[
        Function(
            name="update_user_context",
            description="Provides an updated understanding of the user, and all new information about them from various sources that would've been updated since the chat began. CALL THIS FUNCTION.",
            parameters=[
                FunctionParameterProperties(
                    name="context",
                    type="string",
                    description="A description of all known information about the the user, their current situation, and what they want.",
                    required=True,
                )
            ],
            func=update_user_context,
        )
    ],
)

print(llm("hello"))
# print(llm("I want something that aligns with letting me learn how to code."))
# print(llm("JumpStart doesn't have any oppurtunities for a few months. I want to get started asap."))
