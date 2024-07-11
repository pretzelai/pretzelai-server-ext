import json
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
from tornado.web import HTTPError
from anthropic import NOT_GIVEN, Anthropic, AuthenticationError


import json
from jupyter_server.base.handlers import APIHandler
import tornado
from tornado.web import HTTPError
import anthropic
from fastembed import TextEmbedding


class AnthropicProxyHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            api_key = body.get("api_key")
            messages = body.get("messages")
            max_tokens = body.get("max_tokens", 1024)
            model = body.get("model", "claude-3-5-sonnet-20240620")

            if not api_key or not messages:
                raise HTTPError(400, "Missing required parameters")

            # Extract system message if present
            system_message = None
            filtered_messages = []
            for message in messages:
                if message["role"] == "system":
                    system_message = message["content"]
                else:
                    filtered_messages.append(message)

            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=api_key)

            # Set up streaming response
            self.set_header("Content-Type", "text/event-stream")
            self.set_header("Cache-Control", "no-cache")
            self.set_header("Connection", "keep-alive")

            with client.messages.stream(
                max_tokens=max_tokens,
                messages=filtered_messages,
                model=model,
                system=system_message if system_message else NOT_GIVEN,
            ) as stream:
                for event in stream:
                    self.write(
                        f"event: {event.type}\ndata: {json.dumps(event.model_dump())}\n\n"
                    )
                    await self.flush()

        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

        self.finish()


class AnthropicProxyHandlerSync(APIHandler):
    @tornado.web.authenticated
    def post(self):
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            api_key = body.get("api_key")
            messages = body.get("messages")
            max_tokens = body.get("max_tokens", 1024)
            model = body.get("model", "claude-3-5-sonnet-20240620")

            if not api_key or not messages:
                raise HTTPError(400, "Missing required parameters")

            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=api_key)

            # Make a non-streaming request
            response = client.messages.create(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
            )

            self.write(json.dumps(response.model_dump()))

        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

        self.finish()

    # Override check_xsrf_cookie to disable XSRF check for this handler
    def check_xsrf_cookie(self):
        pass

    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps({"data": "This is /anthropic/complete_nostream endpoint!"})
        )


class FastEmbedHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            texts = body.get("texts")

            if not texts:
                raise HTTPError(400, "Missing required parameter: texts")

            # Initialize the TextEmbedding model
            model = TextEmbedding(model_name="jinaai/jina-embeddings-v2-small-en")

            # Generate embeddings
            embeddings = model.embed(texts)

            # Convert embeddings to list for JSON serialization
            embeddings_list = [emb.tolist() for emb in embeddings]

            self.write(json.dumps({"embeddings": embeddings_list}))

        except Exception as e:
            self.set_status(500)
            self.write(json.dumps({"error": str(e)}))

        self.finish()

    # Override check_xsrf_cookie to disable XSRF check for this handler
    def check_xsrf_cookie(self):
        pass


class AnthropicKeyVerificationHandler(APIHandler):
    @tornado.web.authenticated
    async def post(self):
        try:
            # Parse the request body
            body = json.loads(self.request.body.decode("utf-8"))
            api_key = body.get("api_key")

            if not api_key:
                raise HTTPError(400, "Missing required parameter: api_key")

            # Initialize Anthropic client
            client = Anthropic(api_key=api_key)

            # Attempt to create a simple message to verify the key
            client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=1,
                messages=[{"role": "user", "content": "Hello"}],
            )

            # If we reach here, the key is valid
            self.write(json.dumps({"valid": True}))

        except AuthenticationError:
            # If we get an AuthenticationError, the key is invalid
            self.write(
                json.dumps({"valid": False, "error": "Invalid Anthropic API key"})
            )
        except Exception as e:
            # For any other error, return a 500 status
            self.set_status(500)
            self.write(json.dumps({"valid": False, "error": str(e)}))

        self.finish()

    # Override check_xsrf_cookie to disable XSRF check for this handler
    def check_xsrf_cookie(self):
        pass


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "anthropic", "complete")
    handlers = [
        (url_path_join(base_url, "anthropic", "complete"), AnthropicProxyHandler),
        (
            url_path_join(base_url, "anthropic", "complete_nostream"),
            AnthropicProxyHandlerSync,
        ),
        (
            url_path_join(base_url, "anthropic", "verify_key"),
            AnthropicKeyVerificationHandler,
        ),
        (url_path_join(base_url, "embed"), FastEmbedHandler),
    ]
    web_app.add_handlers(host_pattern, handlers)


# Function to be called when the extension is loaded
def load_jupyter_server_extension(nbapp):
    """
    Called when the extension is loaded.
    Args:
        nbapp (NotebookApp): handle to the Notebook webserver instance.
    """
    setup_handlers(nbapp.web_app)


# download the model at initalization time
TextEmbedding(model_name="jinaai/jina-embeddings-v2-small-en")
