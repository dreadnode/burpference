<img src="assets/dreadburp.jpg" alt="dreadburp" width="300"/>

# Burpference: A Burp Suite Extension

Experimenting with yarrr' Proxy tab going brrrrrrrrrrrrr.

- [Burpference: A Burp Suite Extension](#burpference-a-burp-suite-extension)
- [burpference](#burpference)
  - [Features fit fer a Pirate King:](#features-fit-fer-a-pirate-king)
  - [Prerequisites](#prerequisites)
  - [Setup Guide](#setup-guide)
    - [1. Download and Install Burp Suite](#1-download-and-install-burp-suite)
    - [2. Download and import Jython standalone JAR file](#2-download-and-import-jython-standalone-jar-file)
      - [Steps to Download and Set Up Jython:](#steps-to-download-and-set-up-jython)
    - [3. Add the Burpference Extension to Burp Suite](#3-add-the-burpference-extension-to-burp-suite)
      - [Steps to Add the Extension:](#steps-to-add-the-extension)
  - [Development and known bugs:](#development-and-known-bugs)
  - [Support the Project and Contributing](#support-the-project-and-contributing)

# burpference

Ahoy, mateys! Gather 'round and lend an ear, fer I be here to tell ye ‘bout a treasure chest o' code known as **burpference**. This be no ordinary Burp Suite extension—it be a cunning contraption designed to plunder HTTP responses from Burp’s proxy history (but only in yer chosen waters, savvy?) and send ‘em off to a distant API, all neatly wrapped up in JSON form. It even comes with a trusty GUI, where ye can adjust system prompts, stash yer API keys, choose yer remote hosts, and spy on the logs o’ every intercepted response and the replies from yonder APIs.

- **Snatch Responses Like Booty!** Aye, Burp Suite will be yer trusty lookout, automatically capturing the responses that drift into yer scope. This extension listens close, plucks the details, and hoists ‘em aboard.
- **Send ‘Em Off to the High Seas:** Once ye got yer hands on those responses, ye forward 'em straight to yer configured API endpoint in JSON bottles, complete with any prompts or authentication codes ye need to unlock the treasure.
  - Only what’s in scope be sent, so ye sharpen yer cutlass and avoid wastin’ precious resources on extra inferences, arrr!
  - By default, specific MIME types are excluded ([here](https://github.com/dreadnode/burpference/blob/aafd5ec63af2d658cac2235c5d61ef6238fa6501/burpference/python/burpference.py#L601)).
  - Color me hearties tabs that include `critial/high/medium/low/informational` findings from ye model for easy sights through ya telescopes.
- **Spy on Yer Loot:** There be a log, savvy? Where ye can gaze upon the intercepted responses, the API requests ye sent, and the replies ye got—laid bare fer yer keen pirate eyes to see.
- **Customize to Yer Heart’s Content:** Modify yer system prompts, API key, or remote host as ye see fit. Just hoist yer own configuration files and sail smoothly through yer own custom waters.

---

## Features fit fer a Pirate King:

- Seizes HTTP responses and ships ‘em off in JSON to a remote API—just like sendin' a message in a bottle!
  - Stores inference logs in both the "`Inference Logger`" tab as a live preview and a timestamped file appended to the `/logs` [directory](logs)
- Bring yer own configs, loadin’ and swappin’ system prompts, API keys, and remote hosts like ye be tradin’ treasure maps!
  - Thar's a few examples in the repo itself, feel free to contribute to the project and add additional provider plugins
- A tidy table display of all yer logs, intercepted responses, API calls, and status codes, so ye never lose track of yer engagement.
- Easy setup, runnin’ on Jython, makin’ Python code smooth sailin’ in Burp Suite.

So grab yer compass, hoist the mainsail, and let **burpference** be yer guide as ye plunder the seven seas of HTTP traffic! Arrr!

---

## Prerequisites

Before using **Burpference**, ensure you have:

1. Due to it's awesomeness, burpference may require higher depedencies for system resources to run optimally and especially if using local models.. trust the process and make the machines go brrrrrrrrrrrrr!
2. Installed Burp Suite (Community or Professional edition).
3. Downloaded and set up Jython standalone `.jar` file (a Python interpreter compatible with Java) to run Python-based extensions in Burp Suite.
   1. You do not need Python2.x runtime in your environment for this to work.
4. The [`registerExtenderCallbacks`](https://github.com/dreadnode/burpference/blob/841e5ac63b2785f32ad27746ff217582d3ceb470/burpference/burpference.py#L46-L47) reads a configuration file specific to the remote endpoint's input requirements. Ensure this exists in your environment and Burp has the necessary permissions to access it's location on the filesystem.
   1. **Important**: as Burp Suite cannot read from a filesystem's environment (`os`), you will need to explicitly include them in the configuration `.json` files per-provider.
   2. If you intend to fork or contribute to burpference, ensure that you have excluded the files from git tracking via `.gitignore`
   3. There's also a pre-commit hook in the repo as an additional safety net. Install pre-commit hooks [here](https://pre-commit.com/#install).
5. Setup relevant directory permissions:

`chmod -R 755 logs configs`

6. Ollama locally installed if using this provider plugin, [example config](configs/ollama_mistral-small_latest.json) - ie `ollama run mistral-small` ([docs](https://ollama.com/library/mistral-small)).
   1. Ollama is [now](https://huggingface.co/docs/hub/en/ollama) compatible with any HuggingFace GGUF model which expands the capabilities for using this provider plugin.
      1. There's a template config [here](configs/ollama_huggingface_gguf_template_chat.json) for you to clone and add your own models.

**If using third-party inference, ensure to set a `.env` or environment variables (IE `export OPENAI_API_KEY=""` && `export ANTHROPIC_API_KEY=""`**)

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

Download the latest supported [release candidate](https://github.com/dreadnode/burpference/releases) from the repo and add it as a python-based extension in Burp Suite.

1. Open Burp Suite.
2. Navigate to the Extender tab, then to the Extensions sub-tab.
3. Click on Add to install a new extension.
4. In the dialog box:
   1. Extension Type: Choose [Python](burpference/python).
      Click Next and the extension will be loaded. 🚀

If you prefer to build from source, clone the repo and follow the steps above:

1. Download or clone the **Burpference** project from GitHub:
   ```bash
   git clone https://github.com/dreadnode/burpference.git
   ```

We also recommend setting up a [hotkey](https://portswigger.net/burp/documentation/desktop/settings/ui/hotkeys) in Burp.

---

## Development and known bugs:

Longer-term roadmap is a potential Kotlin-based successor (mainly due to the limitations of Jython in Python2) or compliment burpference.

The below bullets are cool ideas for the repo at a further stage or still actively developing.

- **Scanner**
  - An additional custom one-click "scanner" tab which scans an API target/schema with a selected model and reports findings/payloads and PoCs.
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

The following known issues are something that have been reported so far and marked against issues in the repo.

---

## Support the Project and Contributing

We welcome any issues or contributions to the project, share the treasure! If you like our project, please feel free to drop us some love <3

[![GitHub stars](https://img.shields.io/github/stars/dreadnode/burpference?style=social)](https://github.com/dreadnode/burpference/stargazers)

By watching the repo, you can also be notified of any upcoming releases.

[![Star History Chart](https://api.star-history.com/svg?repos=dreadnode/burpference&type=Date)](https://star-history.com/#dreadnode/burpference&Date)
