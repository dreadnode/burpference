import os
from java.awt import Color

BURPFERENCE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)  # /path/to/burpference/burpference
PROJECT_ROOT = os.path.dirname(BURPFERENCE_DIR)  # /path/to/burpference

CONFIG_DIR = os.path.join(PROJECT_ROOT, "configs")  # /path/to/burpference/configs
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")  # /path/to/burpference/logs
PROMPTS_DIR = os.path.join(PROJECT_ROOT, "prompts")  # /path/to/burpference/prompts
PROXY_PROMPT = os.path.join(PROMPTS_DIR, "proxy_prompt.txt")
SQUID_ASCII_FILE = os.path.join(BURPFERENCE_DIR, "assets", "squid_ascii.txt")

# Color constants
DREADNODE_ORANGE = Color(255, 140, 0)
DREADNODE_PURPLE = Color(128, 0, 128)
DREADNODE_GREY = Color(245, 245, 245)
DREADNODE_RED = Color(239, 86, 47)
DARK_BACKGROUND = Color(40, 44, 52)
LIGHTER_BACKGROUND = Color(50, 55, 65)
TEXT_COLOR = Color(171, 178, 191)
HIGHLIGHT_COLOR = Color(97, 175, 239)

# Severity colors rendered in the 'burpference' tab from the model responses
CRITICAL_COLOR = Color(255, 0, 0)
HIGH_COLOR = Color(255, 69, 0)
MEDIUM_COLOR = Color(255, 165, 0)
LOW_COLOR = Color(255, 255, 0)
INFORMATIONAL_COLOR = Color(200, 200, 200)

# Recommended to tweak this value accordingly to your remote endpoint to prevent breaking token lengths and also maxing local inference resource consumption
MAX_REQUEST_SIZE = 1048576  # 1MB in bytes
