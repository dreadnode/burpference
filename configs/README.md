## Configs

This directory provides some examples from current supported provider plugins for the burpference tool.

**Important**: as Burp Suite cannot read from a filesystem's environment (`os`), you will need to explicitly include them in the configuration `.json` files per-provider. To facilitate the inner setup of these, mimic environment variables are set as placeholders.

If you intend to fork or contribute to burpference, ensure that you have excluded the files from git tracking via `.gitignore`. There's also a pre-commit hook in the repo as an additional safety net.

Install pre-commit hooks [here](https://pre-commit.com/#install).