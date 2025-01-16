import json
from abc import ABCMeta, abstractmethod
import urllib2

# Base class API adapter


class BaseAPIAdapter(object):
    __metaclass__ = ABCMeta

    def __init__(self, config):
        self.config = config

    @abstractmethod
    def prepare_request(self, user_content, system_content=None):
        pass

    @abstractmethod
    def process_response(self, response_data):
        pass


# Ollama /generate API adapter class


class OllamaGenerateAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, system_content, user_content):
        prompt = "{0}\n\nUser request:\n{1}".format(system_content, user_content)
        return {
            "model": self.config.get("model", "llama3.2"),
            "prompt": prompt,
            "format": self.config.get("format", "json"),
            "stream": self.config.get("stream", False),
        }

    def process_response(self, response_data):
        return json.loads(response_data)


# Ollama /chat API adapter class


class OllamaChatAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, system_content, user_content):
        total_input_size = len(system_content) + len(user_content)
        max_tokens = self.config.get(
            "max_input_size", 32000
        )  # Default to 32k if not specified

        if total_input_size > max_tokens:
            raise ValueError(
                "Input size ({total_input_size} chars) exceeds maximum allowed ({max_tokens})"
            )

        model = self.config.get("model", "llama3.2")
        quantization = self.config.get("quantization")
        if model.startswith("hf.co/") or model.startswith("huggingface.co/"):
            if quantization:
                model = "{0}:{1}".format(model, quantization)

        try:
            system_content = system_content.encode("utf-8", errors="replace").decode(
                "utf-8"
            )
            user_content = user_content.encode("utf-8", errors="replace").decode(
                "utf-8"
            )
        except Exception as e:
            raise ValueError("Error encoding content: {str(e)}")

        return {
            "model": model,
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
            "stream": self.config.get("stream", False),
        }

    def process_response(self, response_data):
        return json.loads(response_data)


# OpenAI /v1/chat/completions API adapter class


class OpenAIChatAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, user_content, system_content=None):
        return {
            "model": self.config.get("model", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
        }

    def process_response(self, response_data):
        response = json.loads(response_data)
        if "choices" in response and len(response["choices"]) > 0:
            if "message" in response["choices"][0]:
                return response["choices"][0]["message"]["content"]
            else:
                raise ValueError("Unexpected response format: {response}")
        else:
            raise ValueError("No choices in response: {response}")

    def send_request(self, request_payload):
        headers = {
            "Authorization": "Bearer {0}".format(self.config.get("api_key", "")),
            "Content-Type": "application/json",
        }
        req = urllib2.Request(
            self.config.get("host"), json.dumps(request_payload), headers=headers
        )
        req.get_method = lambda: "POST"
        response = urllib2.urlopen(req)
        return response.read()


# Anthropic /v1/messages API adapter class


class AnthropicAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, user_content, system_content=None):
        return {
            "model": self.config.get("model", "claude-3-5-sonnet-20241022"),
            "max_tokens": int(self.config.get("max_tokens", 1020)),
            "system": system_content,
            "messages": [{"role": "user", "content": user_content}],
        }

    def send_request(self, request_payload):
        headers = {
            "x-api-key": self.config.get("headers", {}).get("x-api-key", ""),
            "content-type": "application/json",
            "anthropic-version": self.config.get("headers", {}).get(
                "anthropic-version", "2023-06-01"
            ),
        }
        req = urllib2.Request(
            self.config.get("host"),
            data=json.dumps(request_payload).encode("utf-8"),
            headers=headers,
        )
        req.get_method = lambda: "POST"
        try:
            response = urllib2.urlopen(req)
            return response.read()
        except urllib2.HTTPError as e:
            error_message = e.read().decode("utf-8")
            raise ValueError("HTTP Error {e.code}: {error_message}")
        except Exception as e:
            raise ValueError("Error sending request: {str(e)}")

    def process_response(self, response_data):
        response = json.loads(response_data)
        if "message" in response:
            return response["message"]["content"]
        elif "content" in response:
            return response["content"]
        else:
            raise ValueError("Unexpected response format: {response}")


# Groq openai/v1/chat/completions


class GroqOpenAIChatAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, user_content, system_content=None):
        return {
            "model": self.config.get("model", "mixtral-8x7b-32768"),
            "max_tokens": int(self.config.get("max_tokens", 1020)),
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
        }

    def process_response(self, response_data):
        response = json.loads(response_data)
        return response["choices"][0]["message"]["content"]

    def send_request(self, request_payload):
        headers = {
            "x-api-key": "{0}".format(self.config.get("api_key", "")),
            "Content-Type": "application/json",
        }
        req = urllib2.Request(
            self.config.get("host"), json.dumps(request_payload), headers=headers
        )
        req.get_method = lambda: "POST"
        response = urllib2.urlopen(req)
        return response.read()


class GroqOpenAIChatAPIStreamAdapter(BaseAPIAdapter):
    def prepare_request(self, system_content, user_content):
        return {
            "model": self.config.get("model", "llama3-8b-8192"),
            "max_tokens": int(self.config.get("max_tokens", 1020)),
            "messages": [
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content},
            ],
        }

    def process_response(self, response_data):
        response = json.loads(response_data)
        return response["choices"][0]["message"]["content"]

    def send_request(self, request_payload):
        headers = {
            "x-api-key": "{0}".format(self.config.get("api_key", "")),
            "Content-Type": "application/json",
        }
        req = urllib2.Request(
            self.config.get("host"), json.dumps(request_payload), headers=headers
        )
        req.get_method = lambda: "POST"
        response = urllib2.urlopen(req)
        return response.read()


# HuggingFace API adapter class /chat-completion


class HuggingFaceAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, user_content, system_content=None):
        messages = []
        if system_content:
            messages.append({"role": "system", "content": system_content})
        messages.append({"role": "user", "content": user_content})

        return {
            "inputs": {"messages": messages},
            "parameters": {
                "max_length": self.config.get("parameters", {}).get("max_length", 512),
                "temperature": self.config.get("parameters", {}).get(
                    "temperature", 0.7
                ),
                "top_p": self.config.get("parameters", {}).get("top_p", 0.9),
                "repetition_penalty": self.config.get("parameters", {}).get(
                    "repetition_penalty", 1.2
                ),
            },
        }

    def send_request(self, request_payload):
        headers = self.config.get("headers", {})

        if "Authorization" not in headers:
            headers["Authorization"] = "Bearer {}".format(
                self.config.get("api_key", "")
            )

        req = urllib2.Request(
            self.config.get("host"),
            json.dumps(request_payload).encode("utf-8"),
            headers=headers,
        )

        try:
            response = urllib2.urlopen(req)
            return response.read()
        except urllib2.HTTPError as e:
            error_message = e.read().decode("utf-8")
            raise ValueError("HTTP Error {}: {}".format(e.code, error_message))

    def process_response(self, response_data):
        response = json.loads(response_data)
        if isinstance(response, list) and len(response) > 0:
            return response[0].get("generated_text", "")
        elif isinstance(response, dict):
            return response.get("generated_text", str(response))
        return str(response)


# Cohere /v2/chat API adapter class
class CohereAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, user_content, system_content=None):
        messages = []
        if system_content:
            messages.append(
                {
                    "role": "SYSTEM",
                    "content": system_content,
                }
            )
        messages.append(
            {
                "role": "USER",
                "content": user_content,
            }
        )

        return {
            "model": self.config.get("model", "command-r-plus-08-2024"),
            "messages": messages,
            "stream": self.config.get("stream", False),
        }

    def process_response(self, response_data):
        response = json.loads(response_data)
        if "text" in response:
            return response["text"]
        elif "response" in response and "text" in response["response"]:
            return response["response"]["text"]
        else:
            raise ValueError("Unexpected response format: %s" % str(response))

    def send_request(self, request_payload):
        headers = self.config.get("headers", {})
        if not headers:
            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization": "Bearer %s" % self.config.get("api_key", ""),
            }

        encoded_data = json.dumps(request_payload).encode("utf-8")
        req = urllib2.Request(
            self.config.get("host"), data=encoded_data, headers=headers
        )

        try:
            response = urllib2.urlopen(req)
            return response.read()
        except urllib2.HTTPError as e:
            error_message = e.read().decode("utf-8")
            raise ValueError("HTTP Error %d: %s" % (e.code, error_message))
        except Exception as e:
            raise ValueError("Error sending request: %s" % str(e))


# Generic other API base adapter


class OtherAPIAdapter(BaseAPIAdapter):
    def prepare_request(self, system_content, user_content):
        # Implement for other API types
        pass

    def process_response(self, response_data):
        # Implement for other API types
        pass


# Function to define and load the API adapter


def get_api_adapter(config):
    api_type = config.get("api_type", "").lower()
    endpoint = config.get("host", "").lower()

    if api_type == "cohere":
        return CohereAPIAdapter(config)
    elif api_type == "ollama":
        if "/generate" in endpoint:
            return OllamaGenerateAPIAdapter(config)
        elif "/chat" in endpoint:
            return OllamaChatAPIAdapter(config)
        else:
            raise ValueError("Unsupported Ollama endpoint: %s" % endpoint)
    elif api_type == "openai":
        return OpenAIChatAPIAdapter(config)
    elif api_type == "anthropic":
        return AnthropicAPIAdapter(config)
    elif api_type == "groq-openai":
        return GroqOpenAIChatAPIAdapter(config)
    elif api_type == "groq-openai-stream":
        return GroqOpenAIChatAPIStreamAdapter(config)
    elif api_type == "huggingface":
        return HuggingFaceAPIAdapter(config)
    elif api_type == "other":
        return OtherAPIAdapter(config)
    else:
        raise ValueError("Unsupported API type: %s" % api_type)
