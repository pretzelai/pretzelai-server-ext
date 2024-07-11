import json
from jupyter_server.base.handlers import APIHandler
from jupyter_server.utils import url_path_join
import tornado
from tornado.web import HTTPError
import anthropic


import json
from jupyter_server.base.handlers import APIHandler
import tornado
from tornado.web import HTTPError
import anthropic


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

            # Initialize Anthropic client
            client = anthropic.Anthropic(api_key=api_key)

            # Set up streaming response
            self.set_header("Content-Type", "text/event-stream")
            self.set_header("Cache-Control", "no-cache")
            self.set_header("Connection", "keep-alive")

            # Stream the response
            with client.messages.stream(
                max_tokens=max_tokens,
                messages=messages,
                model=model,
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

    # Override check_xsrf_cookie to disable XSRF check for this handler
    def check_xsrf_cookie(self):
        pass

    @tornado.web.authenticated
    def get(self):
        self.finish(
            json.dumps({"data": "This is /jupyterlab-examples-server/hello endpoint!"})
        )


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
            json.dumps({"data": "This is /jupyterlab-examples-server/hello endpoint!"})
        )


def setup_handlers(web_app):
    host_pattern = ".*$"
    base_url = web_app.settings["base_url"]
    route_pattern = url_path_join(base_url, "anthropic", "complete")
    handlers = [
        (route_pattern, AnthropicProxyHandler),
        (url_path_join(base_url, "anthropic", "complete2"), AnthropicProxyHandlerSync),
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
