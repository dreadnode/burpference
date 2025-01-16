## Model Configs

This directory provides some examples from current supported provider plugins for the burpference tool.

**Important**: as Burp Suite cannot read from a filesystem's `os` environment, you will need to explicitly define API key values in the configuration `.json` files per-provider (ie, [here](https://github.com/dreadnode/burpference/blob/aafd5ec63af2d658cac2235c5d61ef6238fa6501/configs/anthropic_claude_3_sonnet_20240229.json#L4)). To illustrate only, mimic environment variables are set as placeholders.

If you intend to fork or contribute to burpference, ensure that you have excluded the files from git tracking via `.gitignore`. There's also a pre-commit hook in the repo as an additional safety net. Install pre-commit hooks [here](https://pre-commit.com/#install).

- [Model Configs](#model-configs)
  - [Ollama GGUF](#ollama-gguf)
    - [Example Ollama `/chat` GGUF model:](#example-ollama-chat-gguf-model)
  - [Ollama Inference](#ollama-inference)
    - [Example Ollama `/generate`/`/chat` inference model:](#example-ollama-generatechat-inference-model)
  - [Anthropic Inference](#anthropic-inference)
    - [Example Anthropic `/messages` inference with `claude-3-5-sonnet-20241022`:](#example-anthropic-messages-inference-with-claude-3-5-sonnet-20241022)
  - [OpenAI Inference](#openai-inference)
    - [Example OpenAI `/completions` inference with `gpt-4o-mini`:](#example-openai-completions-inference-with-gpt-4o-mini)
  - [HuggingFace Serveless Inference](#huggingface-serveless-inference)
    - [Example HuggingFace `/text-generation` inference](#example-huggingface-text-generation-inference)
  - [Cohere `/v2/chat` Inference](#cohere-v2chat-inference)
    - [Example Cohere `/v2/chat` inference](#example-cohere-v2chat-inference)
- [Model System Prompts](#model-system-prompts)

---

### Ollama GGUF

#### Example Ollama `/chat` GGUF model:

In order to serve inference as part of burpference, the model must be running on the API endpoint (your local host), ie: "`ollama run hf.co/bartowski/Llama-3.2-1B-Instruct-GGUF:Q4_K_M`".

Ensure to follow steps guidance [here](https://huggingface.co/docs/hub/en/ollama) as a pre-requisite.

```json
{
  "api_type": "ollama",
  "stream": false,
  "host": "http://localhost:11434/api/chat",
  "model": "hf.co/{username}/{repository}", <-- ensure to replace these variables
  "quantization": "Q4_K_M" <-- optional
  "max_input_size": 32000 <-- recommended to adjust based on model loaded and ollama restrictions
}
```

---

### Ollama Inference

#### Example Ollama `/generate`/`/chat` inference model:

In order to serve inference as part of burpference, the model must be running on the API endpoint (your local host), ie: `ollama run mistral-small`.

```json
{
  "api_type": "ollama",
  "format": "json",
  "stream": false,
  "host": "http://localhost:11434/api/generate", <-- adjust based on Ollama API settings, ie: http://localhost:11434/api/chat
  "model": "mistral-small" <-- insert any models from Ollama that are on your local machine
}
```

---

### Anthropic Inference

#### Example Anthropic `/messages` inference with `claude-3-5-sonnet-20241022`:

```json
{
  "api_type": "anthropic",
  "headers": {
    "x-api-key": "{$ANTHROPIC_API_KEY}", <-- replace with your API key in the local config file
    "Content-Type": "application/json",
    "anthropic-version": "2023-06-01"
  },
  "max_tokens": 1020, <-- adjust based on your required usage
  "host": "https://api.anthropic.com/v1/messages",
  "model": "claude-3-5-sonnet-20241022" <-- adjust based on your required usage
}
```

---

### OpenAI Inference

#### Example OpenAI `/completions` inference with `gpt-4o-mini`:

```json
{
  "api_type": "openai",
  "headers": {
    "Authorization": "Bearer {$OPENAI_API_KEY}", <-- replace with your API key in the local config file
    "Content-Type": "application/json"
  },
  "stream": false,
  "host": "https://api.openai.com/v1/chat/completions",
  "model": "gpt-4o-mini", <-- adjust based on your required usage
  "temperature": 0.1 <-- adjust based on your required usage
}
```

### HuggingFace Serveless Inference

#### Example HuggingFace `/text-generation` inference

```json
{
    "api_type": "huggingface",
    "name": "HuggingFace Code Review",
    "model": "bigcode/starcoder",
    "host": "https://api-inference.huggingface.co/models/bigcode/starcoder",
    "headers": {
        "Authorization": "YOUR_HUGGINGFACE_API_KEY",
        "Content-Type": "application/json"
    },
    "parameters": {
        "max_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.9,
        "repetition_penalty": 1.2,
        "do_sample": true
    }
}
```

### Cohere `/v2/chat` Inference

#### Example Cohere `/v2/chat` inference

```json
{
    "api_type": "cohere",
    "headers": {
        "Authorization": "bearer CO_API_KEY",
        "accept": "application/json",
        "content-type": "application/json"
    },
    "host": "https://api.cohere.com/v2/chat",
    "model": "command-r-plus-08-2024",
    "stream": false
}
```

## Model System Prompts

By default, the system prompt sent as pretext to the model is defined [here](../prompts/proxy_prompt.txt), feel free to edit, tune and tweak as you see fit. This is also true for the scanner extension tab.

---