import os
from java.awt import Color

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(ROOT_DIR, "configs")
LOG_DIR = os.path.join(ROOT_DIR, "logs")
PROXY_PROMPT = os.path.join(ROOT_DIR, "prompts/proxy_prompt.txt")

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

SQUID_ASCII_FILE = os.path.join(ROOT_DIR, "assets", "squid_ascii.txt")

# Recommended to tweak this value accordingly to your remote endpoint to prevent breaking token lengths and also maxing local inference resource consumption
MAX_REQUEST_SIZE = 1048576  # 1MB in bytes
