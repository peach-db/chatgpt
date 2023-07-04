# Chat API

API for a conversational chatbot that understands personalized information about the user, and keeps it updated as the conversation progresses. Here, we will guide you through the API endpoints and their respective usages.

## API Endpoints

### Users

#### 1. Create User

URL: `/user`

Method: `POST`

Request Body:

```json
{
  "context": "string"
}
```

Response Body:

```json
{
  "user_id": "string"
}
```

This endpoint creates a new user based on the given context (personal information) and returns a unique user_id.

Example:

Request

```json
{
  "context": "John Doe is 27 years old. He is a university student. He has a university education and his goal is to buy some shiny tech in 2 months."
}
```

Response

```json
{
  "user_id": "b87cc08e-d41f-4fbd-a696-eeedd89e0650"
}
```

#### 2. Get User Information

URL: `/user/{user_id}`

Method: `GET`

Path Parameters:

- user_id: The unique identifier of the user

Response Body:

```json
{
  "user_context": "string"
}
```

This endpoint retrieves a user's information based on their user_id.

#### 3. Update User

URL: `/user/{user_id}`

Method: `PUT`

Path Parameters:

- user_id: The unique identifier of the user

Request Body:

```json
{
  "context": "string"
}
```

This endpoint updates a user's information based on their user_id.

#### 4. Delete User

URL: `/user/{user_id}`

Method: `DELETE`

Path Parameters:

- user_id: The unique identifier of the user

This endpoint deletes a user based on their user_id.

### Documents

#### 1. Create Document

URL: `/doc`

Method: `POST`

Request Body:

```json
{
  "value": ["string"]
}
```

Response Body:

```json
{
  "doc_ids": ["string"]
}
```

This endpoint creates one or more documents containing available opportunities and returns a list of unique doc_ids.

Example:

Request

```json
{
  "value": ["Document 1 content", "Document 2 content"]
}
```

Response

```json
{
  "doc_ids": [
    "a29305d7-8801-4a3e-a605-1a5a8fcfc476",
    "b6a21448-6e05-4777-baf8-0a94d8370030"
  ]
}
```

#### 2. Get Document

URL: `/doc/{doc_id}`

Method: `GET`

Path Parameters:

- doc_id: The unique identifier of the document

Response Body:

```json
{
  "document": "string",
  "num_tokens": "int"
}
```

This endpoint retrieves a document's content based on its doc_id. It additionally provides the number of tokens used by the document.

#### 3. Update Document

URL: `/doc/{doc_id}`

Method: `PUT`

Path Parameters:

- doc_id: The unique identifier of the document

Request Body:

```json
{
  "value": "string"
}
```

This endpoint updates a document's content based on its doc_id.

#### 4. Delete Document

URL: `/doc/{doc_id}`

Method: `DELETE`

Path Parameters:

- doc_id: The unique identifier of the document

This endpoint deletes a document based on its doc_id.

#### 5. Empty All Documents

URL: `/doc-all`

Method: `DELETE`

This endpoint deletes all documents in the collection.

#### 6. Get Info about Collection of Documents

URL: `/doc`

Method: `GET`

This endpoint returns information about the collection of documents (such as number of documents in it).

#### 6. Get all Documents

URL: `/doc-all`

Method: `GET`

This endpoint returns all documents currently loaded into database. Each item returns as a tuple of its ID, content, as well as the number of tokens used by that document. This endpoint also separately returns `total_tokens`.

Response Body:

```json
{
  "items": [["str", "str", "int"]], // (id, doc, number of tokens)
  "total_tokens": "int"
}
```

### Bots

#### 1. Create Bot

URL: `/bot`

Method: `POST`

Request Body:

```json
{
  "system_prompt": "string"
}
```

Response Body:

```json
{
  "bot_id": "string"
}
```

This endpoint creates a new bot with a specific system_prompt and returns a unique bot_id. The system_prompt should contain placeholders `{user_context}` and `{document_context}`.

Example:

Request

```json
{
  "system_prompt": "Bot description with {user_context} and {document_context} placeholders."
}
```

Response

```json
{
  "bot_id": "efdde75c-b393-418d-a887-77dc93bc4b97"
}
```

#### 2. Chat with Bot

URL: `/bot/{bot_id}/chat/{user_id}`

Method: `POST`

Path Parameters:

- bot_id: The unique identifier of the bot
- user_id: The unique identifier of the user

Request Body:

```json
{
  "query": "string"
}
```

Response Body:

```json
{
  "response": "string"
}
```

This endpoint interacts with the bot to chat for a specific user_id and bot_id. It accepts a query message from the user and returns a response message from the bot. Hitting the same endpoint continuously maintains the conversation history and user context.

Example:

Request

```json
{
  "query": "hello!"
}
```

Response

```json
{
  "response": "Hi there! ..."
}
```

## Usage Workflow

1. Create a user with their personal information.
2. Add available opportunities in ProGrad as documents.
3. Create a bot with a specific system_prompt.
4. Interact with the bot using the `/bot/{bot_id}/chat/{user_id}` endpoint to maintain the conversation history and user context.

Feel free to experiment with the provided endpoints and adapt them to your particular use case. The API is designed to cater to millions of users and can be modified to better suit your needs.
