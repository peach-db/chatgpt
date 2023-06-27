import os
import shelve
from typing import Annotated
from uuid import uuid4

import dotenv
import fastapi
import fastapi.middleware.cors
import uvicorn
from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field
from rich import print

from chatgpt import ChatGPT, Function, FunctionParameterProperties

dotenv.load_dotenv()

APP_PORT = 58000

app = fastapi.FastAPI()
app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=["*", f"http://localhost:{APP_PORT}", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

USER_SHELVE_PATH = "user.db"
DOCS_SHELVE_PATH = "docs.db"
BOT_SHELVE_PATH = "bot.db"
# TODO: refactor maybe include in "user.db". Not done here as updating a list in shelve is problematic.
HISTORY_SHELVE_PATH = "history.db"
USER_NOT_FOUND_ERROR_STR = "User not found"
DOC_NOT_FOUND_ERROR_STR = "Document not found"

### User CRUD ###


class User(BaseModel):
    context: str


def _generate_unique_id(existing_ids: list):
    id = str(uuid4())
    if not existing_ids:
        return id
    else:
        while id in existing_ids:
            id = str(uuid4())
        return id


@app.post("/user/")
async def create_user(item: User):
    with shelve.open(USER_SHELVE_PATH) as db:
        user_id = _generate_unique_id(existing_ids=list(db.keys()))
        db[user_id] = item.context

    return {"user_id": user_id}


@app.get("/user/{user_id}")
async def get_user(user_id: str):
    with shelve.open(USER_SHELVE_PATH) as db:
        if user_id not in db:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_ERROR_STR)
        else:
            user_context = db[user_id]
    return {"user_context": user_context}


@app.put("/user/{user_id}")
async def update_user(user_id: str, item: User):
    with shelve.open(USER_SHELVE_PATH) as db:
        if user_id not in db:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_ERROR_STR)
        else:
            db[user_id] = item.context

    return Response(status_code=200)


@app.delete("/user/{user_id}")
async def delete_user(user_id: str):
    with shelve.open(USER_SHELVE_PATH) as db:
        if user_id not in db:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_ERROR_STR)
        else:
            del db[user_id]

    return Response(status_code=200)


### Document CRUD ###


class Document(BaseModel):
    value: str | list[str]


@app.post("/doc/")
async def create_doc(item: Document):
    with shelve.open(DOCS_SHELVE_PATH) as db:
        if isinstance(item.value, str):
            values = [item.value]
        else:
            assert isinstance(item.value, list)
            values = item.value

        doc_ids = []
        for val in values:
            doc_id = _generate_unique_id(existing_ids=list(db.keys()))
            db[doc_id] = val
            doc_ids.append(doc_id)

    return {"doc_ids": doc_ids}


@app.get("/doc/")
async def get_doc_info():
    info = {}
    with shelve.open(DOCS_SHELVE_PATH) as db:
        info["num_docs"] = len(db.keys())

    return info

@app.get("/doc-all")
async def get_all_docs():
    with shelve.open(DOCS_SHELVE_PATH) as db:
        if len(db.keys()) == 0:
            raise HTTPException(status_code=404, detail="Documents are empty. Please add some documents.")
        else:
            return list(db.items())


@app.get("/doc/{doc_id}")
async def read_doc(doc_id: str):
    with shelve.open(DOCS_SHELVE_PATH) as db:
        if doc_id not in db:
            raise HTTPException(status_code=404, detail=DOC_NOT_FOUND_ERROR_STR)
        else:
            document = db[doc_id]

    return {"document": document}


@app.put("/doc/{doc_id}")
async def update_doc(doc_id: str, item: Document):
    with shelve.open(DOCS_SHELVE_PATH) as db:
        if doc_id not in db:
            raise HTTPException(status_code=404, detail=DOC_NOT_FOUND_ERROR_STR)
        else:
            db[doc_id] = item.value

    return Response(status_code=200)


@app.delete("/doc/{doc_id}")
async def delete_doc(doc_id: str):
    with shelve.open(DOCS_SHELVE_PATH) as db:
        if doc_id not in db:
            raise HTTPException(status_code=404, detail=DOC_NOT_FOUND_ERROR_STR)
        else:
            del db[doc_id]

    return Response(status_code=200)


# TODO: maybe accept an expression in the above endpoint so we can delete anything that matches?
@app.delete("/doc-all")
async def delete_all_docs():
    with shelve.open(DOCS_SHELVE_PATH) as db:
        db.clear()

    return Response("All documents deleted.", status_code=200)


### BOT ENDPOINTS ###


class BotCreationRequest(BaseModel):
    system_prompt: Annotated[
        str, Field(description="A system prompt that contains placeholders for `user_context` and `document_context`.")
    ]


@app.post("/bot")
async def create_bot(request: BotCreationRequest):
    """
    Create a new bot given a specific system prompt that contains placeholders for `user_context` and `document_context`.
    Returns a `bot_id` that can be used along with `user_id` to chat with the bot.
    """
    with shelve.open(BOT_SHELVE_PATH) as db:
        bot_id = _generate_unique_id(existing_ids=list(db.keys()))
        db[bot_id] = request.system_prompt

        # TODO: generalise for finding more than 1, and listing them.
        if ("{user_context}" not in db[bot_id]) or ("{document_context}" not in db[bot_id]):
            raise HTTPException(
                status_code=400, detail="System prompt must contain {user_context} and {document_context}."
            )

    return {"bot_id": bot_id}


def _update_user_context(user_id: str, context: str = ""):
    if len(context) == 0:
        raise HTTPException(status_code=400, detail="OpenAI returned empty context. Error!")

    with shelve.open(USER_SHELVE_PATH) as db:
        if user_id not in db:
            raise HTTPException(status_code=404, detail=USER_NOT_FOUND_ERROR_STR)
        else:
            # TODO: use list instead? so we can keep record of old contexts?
            db[user_id] = context

    return context


class ConversationRequest(BaseModel):
    query: str


@app.post("/bot/{bot_id}/chat/{user_id}")
async def chat(bot_id: str, user_id: str, request: ConversationRequest):
    """
    Chat interaction for a specific `system_prompt` and `user_context`. Returns a `response` from the bot.
    Hitting the same end-point continuously maintains the conversation history and user context.
    """
    # TODO: what if user wants to restart conversation?
    with shelve.open(BOT_SHELVE_PATH) as db:
        if bot_id not in db:
            raise HTTPException(status_code=404, detail="Bot not found")
        else:
            system_prompt = db[bot_id]

    with shelve.open(USER_SHELVE_PATH) as db:
        if user_id not in db:
            raise HTTPException(status_code=404, detail="User not found")
        else:
            user_context = db[user_id].strip()

    with shelve.open(DOCS_SHELVE_PATH) as db:
        if len(db.keys()) == 0:
            raise HTTPException(status_code=404, detail="Documents are empty. Please add some documents.")
        else:
            document_context = "\n".join([str(v).strip() for _, v in db.items()])

    system_prompt = system_prompt.replace("{user_context}", user_context)
    system_prompt = system_prompt.replace("{document_context}", document_context)

    # Maintains conversation history.
    # TODO: this is overkill given we're maintain updated user_context as well.
    history_db_key = str((user_id, bot_id))
    with shelve.open(HISTORY_SHELVE_PATH) as db:
        if history_db_key in db and len(db[history_db_key]) > 0:
            messages = [{"role": "system", "content": system_prompt}] + db[history_db_key]

            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == system_prompt
            system_prompt = None
        else:
            messages = None
            db[history_db_key] = []

    # TODO: ugly. clean-up!
    def update_user_context(context: str = ""):
        return _update_user_context(user_id=user_id, context=context)

    llm = ChatGPT(
        model="gpt-4-0613",
        system_prompt=system_prompt,
        messages=messages,
        temperature=0,
        call_fn_on_every_user_message="update_user_context",
        functions=[
            Function(
                name="update_user_context",
                description=os.environ.get("UPDATE_USER_CONTEXT_FN_DESCRIPTION"),
                parameters=[
                    FunctionParameterProperties(
                        name="context",
                        type="string",
                        description=os.environ.get("UPDATE_USER_CONTEXT_FN_CTX_PARAM_DESCRIPTION"),
                        required=True,
                    )
                ],
                func=update_user_context,
            )
        ],
    )
    result = llm(request.query)

    with shelve.open(HISTORY_SHELVE_PATH) as db:
        db[history_db_key] = llm.messages

    return {"response": result[-1]["content"]}


if __name__ == "__main__":
    uvicorn.run("api:app", port=APP_PORT, reload=True)
