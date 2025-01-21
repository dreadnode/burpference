# burpference

<p align="center">
    <img
    src="https://d1lppblt9t2x15.cloudfront.net/logos/5714928f3cdc09503751580cffbe8d02.png"
    alt="Logo"
    align="center"
    width="144px"
    height="144px"
    />
</p>

<div align="center">

[![GitHub release (latest by date)](https://img.shields.io/github/v/release/dreadnode/burpference)](https://github.com/dreadnode/burpference/releases)
[![GitHub stars](https://img.shields.io/github/stars/dreadnode/burpference?style=social)](https://github.com/dreadnode/burpference/stargazers)
[![GitHub license](https://img.shields.io/github/license/dreadnode/burpference)](https://img.shields.io/github/license/dreadnode/burpference)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/dreadnode/burpference/pulls)

Experimenting with yarrr' Burp Proxy tab going brrrrrrrrrrrrr.

</div>

- [burpference](#burpference)
  - [Prerequisites](#prerequisites)
  - [Setup Guide](#setup-guide)
    - [1. Download and Install Burp Suite](#1-download-and-install-burp-suite)
    - [2. Download and import Jython standalone JAR file](#2-download-and-import-jython-standalone-jar-file)
      - [Steps to Download and Set Up Jython:](#steps-to-download-and-set-up-jython)
    - [3. Add the Burpference Extension to Burp Suite](#3-add-the-burpference-extension-to-burp-suite)
      - [Steps to Add the Extension:](#steps-to-add-the-extension)
    - [4. Setup your configs](#4-setup-your-configs)
      - [Checkout the config docs:](#checkout-the-config-docs)
    - [5. Additional options:](#5-additional-options)
  - [Development and known bugs:](#development-and-known-bugs)
  - [Support the Project and Contributing](#support-the-project-and-contributing)
    - [Star History](#star-history)

<br>

"_burpference_" started as a research idea of offensive agent capabilities and is a fun take on Burp Suite and running inference. The extension is open-source and designed to capture in-scope HTTP requests and responses from Burp's proxy history and ship them to a remote LLM API in JSON format. It's designed with a flexible approach where you can configure custom system prompts, store API keys and select remote hosts from numerous model providers as well as the ability for you to create your own API configuration. The idea is for an LLM to act as an agent in an offensive web application engagement to leverage your skills and surface findings and lingering vulnerabilities. By being able to create your own configuration and model provider allows you to also host models locally via Ollama to prevent potential high inference costs and potential network delays or rate limits.

Some key features:

- **Automated Response Capture**: Burp Suite acts as your client monitor, automatically capturing responses that fall within your defined scope. This extension listens for, captures, and processes these details with an offensive-focused agent.
- **API Integration**: Once requests and response streams are captured, they are packaged and forwarded to your configured API endpoint in JSON format, including any necessary system-level prompts or authentication tokens.
  - Only in-scope items are sent, optimizing resource usage and avoiding unnecessary API calls.
  - By default, [certain MIME types are excluded](https://github.com/dreadnode/burpference/blob/7e81641e263bbdfe4a38e30746eb3c27f3454190/burpference/burpference.py#L616).
  - Color-coded tabs display `critical/high/medium/low/informational` findings from your model for easy visualization.
- **Scanner Analysis**: A dedicated scanner tab provides focused security analysis capabilities:
  - Direct analysis of URLs and OpenAPI specifications
  - Load the configuration files using the API adapter, the same as usual in burpference for efficient management of API keys/model selection etc
  - Automated extraction of security headers and server information
  - Real-time security header assessment (X-Frame-Options, CSP, HSTS, etc.)
  - Custom system prompts for specialized analysis scenarios
  - Support for both single-endpoint and full domain scanning
  - Integration with Burp's native issue reporting system
- **Comprehensive Logging**: A logging system allows you to review intercepted responses, API requests sent, and replies received—all clearly displayed for analysis.
  - A clean table interface displaying all logs, intercepted responses, API calls, and status codes for comprehensive engagement tracking.
  - Stores inference logs in both the "_Inference Logger_" tab as a live preview and a timestamped file in the /logs directory.
- **Native Burp Reporting**: burpference' system prompt invokes the model to make an assessment based on severity level of the finding which is color-coded (a heatmap related to the severity level) in the extenstion tab.
  - Additionally, burpference "findings" are created as issues in the Burp Scanner navigation bar available across all tabs in the Burp UI.
- **Flexible Configuration**: Customize system prompts, API keys, or remote hosts as needed. Use your own configuration files for seamless integration with your workflow.
  - Supports custom configurations, allowing you to load and switch between system prompts, API keys, and remote hosts
    - [Several examples](configs/README.md) are provided in the repository, and contributions for additional provider plugins are welcome.
- **Flexible System Prompts**: Specialized [prompt](./prompts/) templates for focused API security testing with some examples:
  - Authentication bypass and access control analysis
  - Sensitive data exposure and PII leakage detection
  - Injection vulnerability assessment across all vectors
  - Additional templates can be created for specific testing scenarios
    - Dynamic prompt switching during runtime to tailor analysis based on target endpoints

So grab yer compass, hoist the mainsail, and let **burpference** be yer guide as ye plunder the seven seas of HTTP traffic! Yarrr'!

---

## Prerequisites

Before using **Burpference**, ensure you have the following:

1. Due to it's awesomeness, burpference may require higher system resources to run optimally, especially if using local models. Trust the process and make the machines go brrrrrrrrrrrrr!
2. Installed Burp Suite (Community or Professional edition).
3. Downloaded and set up Jython standalone `.jar` file (a Python interpreter compatible with Java) to run Python-based extensions in Burp Suite.
   1. You do not need Python2.x runtime in your environment for this to work.
4. The [`registerExtenderCallbacks`](https://github.com/dreadnode/burpference/blob/7e81641e263bbdfe4a38e30746eb3c27f3454190/burpference/burpference.py#L54) reads a configuration file specific to the remote endpoint's input requirements. Ensure this exists in your environment and Burp has the necessary permissions to access it's location on the filesystem.
   1. **Important**: as Burp Suite cannot read from a filesystem's `os` environment, you will need to explicitly include API key values in the configuration `.json` files per-provider.
   2. If you intend to fork or contribute to burpference, ensure that you have excluded the files from git tracking via `.gitignore`.
   3. There's also a pre-commit hook in the repo as an additional safety net. Install pre-commit hooks [here](https://pre-commit.com/#install).
5. Setup relevant directory permissions for burpference to create log files:

`chmod -R 755 logs configs`

**In some cases when loading the extension you may experience directory permission write issues and as such its recommended to restart Burp Suite following the above.**

6. Ollama locally installed if using this provider plugin, [example config](configs/ollama_mistral-small.json) and the model running locally - ie `ollama run mistral-small` ([model docs](https://ollama.com/library/mistral-small)).
   1. Ollama is [now](https://huggingface.co/docs/hub/en/ollama) compatible with any HuggingFace GGUF model which expands the capabilities for using this provider plugin.
      1. There's a template config [here](configs/README.md#ollama-gguf) for you to clone and add your own models.

---

## Setup Guide

### 1. Download and Install Burp Suite

If Burp Suite is not already installed, download it from:
[Burp Suite Community/Professional](https://portswigger.net/burp/communitydownload)

---

### 2. Download and import Jython standalone JAR file

Jython enables Burp Suite to run Python-based extensions. You will need to download and configure it within Burp Suite.

#### Steps to Download and Set Up Jython:

1. Go to the [Jython Downloads Page](https://www.jython.org/download).
2. Download the standalone Jython `.jar` file (e.g., `jython-standalone-2.7.4.jar`).
3. Open Burp Suite.
4. Go to the `Extensions` tab in Burp Suite.
5. Under the `Options` tab, scroll down to the **Python Environment** section.
6. Click **Select File**, and choose the `jython-standalone-2.7.4.jar` file you just downloaded.
7. Click **Apply** to load the Jython environment into Burp Suite.

---

### 3. Add the Burpference Extension to Burp Suite

#### Steps to Add the Extension:

Download the latest supported [release](https://github.com/dreadnode/burpference/releases) from the repo, unzip it and add it as a python-based extension in Burp Suite. **It's recommended to save this in a `~/git` directory based on the current code and how the logs and configs are structured.**

1. Open Burp Suite.
2. Navigate to the Extensions tab.
3. Click on Add to install a new extension.
4. In the dialog box:
   1. Extension Type: Choose Python and the `burpference/burpference.py` file, this will instruct Burp Suite to initialize the extension by invoking the `registerExtenderCallbacks` method.
      Click Next and the extension will be loaded. 🚀

If you prefer to build from source, clone the repo and follow the steps above:

1. Download or clone the **Burpference** project from GitHub:

   ```bash
   git clone https://github.com/dreadnode/burpference.git
   ```

### 4. Setup your configs

#### Checkout the config docs:

Head over to the [configuration docs](./configs/README.md)!

### 5. Additional options:

We also recommend setting up a custom [hotkey](https://portswigger.net/burp/documentation/desktop/settings/ui/hotkeys) in Burp to save clicks.

---

## Development and known bugs:

Longer-term roadmap is a potential Kotlin-based successor (mainly due to the limitations of Jython with the [Extender API](https://portswigger.net/burp/extender/api/)) or additionally, compliment burpference.

The below bullets are cool ideas for the repo at a further stage or still actively developing.

- **Conversations**
  - Enhanced conversation turns with the model to reflect turns for both HTTP requests and responses to build context.
- **Prompt Tuning**:
  - Modularize a centralized source of prompts sent to all models.
  - Grounding and context: Equip the model with context, providing links to OpenAPI schemas and developer documentation.
- **Offensive Agents and Tool Use**
  - Equip agents with burpference results detail and tool use for weaponization and exploitation phase.
- **Optimization**:
  - Extend functionality of selecting multiple configurations and sending results across multiple endpoints for optimal results.
  - Introduce judge reward systems for findings.

---

## Support the Project and Contributing

We welcome any issues or contributions to the project, share the treasure! If you like our project, please feel free to drop us some love <3

### Star History

[![GitHub stars](https://img.shields.io/github/stars/dreadnode/burpference?style=social)](https://github.com/dreadnode/burpference/stargazers)

By watching the repo, you can also be notified of any upcoming releases.

<img src="https://api.star-history.com/svg?repos=dreadnode/burpference&type=Date" width="600" height="400">
