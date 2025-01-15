import os
from javax.swing import (
    JPanel,
    JLabel,
    JTextArea,
    JScrollPane,
    JButton,
    JComboBox,
    BoxLayout,
    JTextField,
    ButtonGroup,
    JRadioButton,
)
from java.awt import BorderLayout, FlowLayout, Dimension
from java.lang import Short
from threading import Thread
import json
import urllib2
import re
from javax.swing.border import EmptyBorder

SCANNER_PROMPT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "scanner_prompt.txt"
)
OPENAPI_PROMPT = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "prompts", "openapi_prompt.txt"
)


class BurpferenceScanner:
    def __init__(self, callbacks, helpers, config, api_adapter, colors=None):
        self._callbacks = callbacks
        self._helpers = helpers
        self.config = config
        self.api_adapter = api_adapter
        self._hosts = set()
        self._last_prompt_content = None
        self._last_openapi_content = None

        self.colors = colors or {}
        self.DARK_BACKGROUND = self.colors.get("DARK_BACKGROUND")
        self.LIGHTER_BACKGROUND = self.colors.get("LIGHTER_BACKGROUND")
        self.DREADNODE_GREY = self.colors.get("DREADNODE_GREY")
        self.DREADNODE_ORANGE = self.colors.get("DREADNODE_ORANGE")

    def add_host(self, host):
        """Add a host to the scanner's tracked hosts"""
        if host not in self._hosts:
            self._hosts.add(host)
            if hasattr(self, "_domain_selector"):
                self._domain_selector.removeAllItems()
                for h in sorted(self._hosts):
                    self._domain_selector.addItem(h)

    def create_scanner_tab(self):
        """Creates the security analysis scanner tab"""
        panel = JPanel()
        panel.setLayout(BorderLayout())
        panel.setBackground(self.DARK_BACKGROUND)

        # Create a top container for config and input sections
        top_container = JPanel()
        top_container.setLayout(BoxLayout(top_container, BoxLayout.Y_AXIS))
        top_container.setBackground(self.DARK_BACKGROUND)
        # Set maximum height for top container to keep it compact
        top_container.setMaximumSize(Dimension(Short.MAX_VALUE, 300))

        # Config info panel
        config_info_panel = JPanel(FlowLayout(FlowLayout.LEFT, 5, 2))
        config_info_panel.setBackground(self.DARK_BACKGROUND)
        self.config_label = JLabel(self.get_config_status())
        self.config_label.setForeground(self.DREADNODE_ORANGE)
        config_info_panel.add(self.config_label)
        config_info_panel.setMaximumSize(Dimension(Short.MAX_VALUE, 25))

        # Target input section
        target_panel = JPanel(FlowLayout(FlowLayout.LEFT, 5, 2))
        target_panel.setBackground(self.DARK_BACKGROUND)

        config_info_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        config_info_panel.setBackground(self.DARK_BACKGROUND)
        self.config_label = JLabel(self.get_config_status())
        self.config_label.setForeground(self.DREADNODE_ORANGE)
        config_info_panel.add(self.config_label)

        # Input type selection
        type_panel = JPanel()
        type_panel.setBackground(self.DARK_BACKGROUND)
        type_group = ButtonGroup()

        self.url_radio = JRadioButton("URL", True)
        self.url_radio.setBackground(self.DARK_BACKGROUND)
        self.url_radio.setForeground(self.DREADNODE_ORANGE)

        self.openapi_radio = JRadioButton("OpenAPI URL", False)
        self.openapi_radio.setBackground(self.DARK_BACKGROUND)
        self.openapi_radio.setForeground(self.DREADNODE_ORANGE)

        type_group.add(self.url_radio)
        type_group.add(self.openapi_radio)
        type_panel.add(self.url_radio)
        type_panel.add(self.openapi_radio)

        # Target input
        target_label = JLabel("Target:")
        target_label.setForeground(self.DREADNODE_GREY)
        self._target_input = JTextField(40)
        self._target_input.setBackground(self.LIGHTER_BACKGROUND)
        self._target_input.setForeground(self.DREADNODE_ORANGE)

        target_panel.add(type_panel)
        target_panel.add(target_label)
        target_panel.add(self._target_input)
        target_panel.setMaximumSize(Dimension(Short.MAX_VALUE, 35))

        # System prompt panel
        prompt_panel = JPanel()
        prompt_panel.setLayout(BoxLayout(prompt_panel, BoxLayout.Y_AXIS))
        prompt_panel.setBackground(self.DARK_BACKGROUND)

        prompt_desc = JLabel(
            "Current system prompt for analysis. Modifies the model's behavior and focus areas."
        )
        prompt_desc.setForeground(self.DREADNODE_GREY)
        prompt_label = JLabel("System Prompt:")
        prompt_label.setForeground(self.DREADNODE_GREY)

        self._custom_prompt = JTextArea(8, 50)
        self._custom_prompt.setLineWrap(True)
        self._custom_prompt.setWrapStyleWord(True)
        self._custom_prompt.setBackground(self.LIGHTER_BACKGROUND)
        self._custom_prompt.setForeground(self.DREADNODE_ORANGE)

        # Load and set initial prompt content
        initial_prompt = self.load_prompt_template(self.openapi_radio.isSelected())
        if initial_prompt:
            self._custom_prompt.setText(initial_prompt)
            # Store as last content so we can detect changes
            if self.openapi_radio.isSelected():
                self._last_openapi_content = initial_prompt
            else:
                self._last_prompt_content = initial_prompt

        prompt_scroll = JScrollPane(self._custom_prompt)
        prompt_scroll.setPreferredSize(Dimension(600, 200))
        prompt_scroll.setMaximumSize(Dimension(Short.MAX_VALUE, 200))

        # Button panel
        button_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        button_panel.setBackground(self.DARK_BACKGROUND)
        scan_button = JButton(
            "Start Security Analysis", actionPerformed=self.analyze_target
        )
        scan_button.setBackground(self.DREADNODE_ORANGE)
        scan_button.setForeground(self.DREADNODE_GREY)
        button_panel.add(scan_button)
        button_panel.setMaximumSize(Dimension(Short.MAX_VALUE, 35))

        # Results area - should take most space
        self._scanner_output = JTextArea(20, 50)
        self._scanner_output.setEditable(False)
        self._scanner_output.setLineWrap(True)
        self._scanner_output.setWrapStyleWord(True)
        self._scanner_output.setBackground(self.LIGHTER_BACKGROUND)
        self._scanner_output.setForeground(self.DREADNODE_ORANGE)
        scanner_scroll = JScrollPane(self._scanner_output)

        # Layout
        prompt_panel.add(prompt_desc)
        prompt_panel.add(prompt_label)

        top_container.add(config_info_panel)
        top_container.add(target_panel)
        top_container.add(prompt_panel)
        top_container.add(prompt_scroll)
        top_container.add(button_panel)

        panel.add(top_container, BorderLayout.NORTH)
        panel.add(scanner_scroll, BorderLayout.CENTER)

        return panel

    def analyze_target(self, event):
        """Handles the security analysis request"""
        if not self.api_adapter:
            self._scanner_output.setText(
                "Error: No API adapter configured. Debug info:\n"
                "Config: %s\nAPI Adapter: %s"
                % (
                    json.dumps(self.config, indent=2) if self.config else "None",
                    str(self.api_adapter),
                )
            )
            return

        if not self.config:
            self._scanner_output.setText(
                "Error: No configuration loaded. Please select a configuration file first."
            )
            return

        target = self._target_input.getText().strip()
        if not target:
            self._scanner_output.setText("Please enter a target URL")
            return

        is_openapi = self.openapi_radio.isSelected()
        custom_prompt = self._custom_prompt.getText().strip()

        def run_analysis():
            self._scanner_output.setText(
                "Analyzing %s %s...\n" % ("OpenAPI at" if is_openapi else "", target)
            )
            try:
                if is_openapi:
                    content = self.fetch_openapi_spec(target)
                    if not content:
                        return
                    prompt = (
                        custom_prompt
                        if custom_prompt
                        else "Analyze this OpenAPI specification for security vulnerabilities, authentication issues, and potential misconfigurations:"
                    )
                else:
                    content = self.analyze_url(target)
                    if not content:
                        return
                    prompt = (
                        custom_prompt if custom_prompt else self.load_prompt_template()
                    )

                # Prepare request for the model
                analysis_request = self.api_adapter.prepare_request(
                    user_content=json.dumps(content, indent=2), system_content=prompt
                )

                # Send to configured model
                req = urllib2.Request(self.config.get("host", ""))
                for header, value in self.config.get("headers", {}).items():
                    req.add_header(header, value)

                response = urllib2.urlopen(req, json.dumps(analysis_request))
                response_data = response.read()
                analysis = self.api_adapter.process_response(response_data)

                self._scanner_output.setText(
                    "Security Analysis for %s:\n\n%s" % (target, analysis)
                )

            except urllib2.URLError as e:
                self._scanner_output.setText("Error connecting to target: %s" % str(e))
            except ValueError as e:
                self._scanner_output.setText("Error processing response: %s" % str(e))
            except Exception as e:
                self._scanner_output.setText("Error during analysis: %s" % str(e))

        Thread(target=run_analysis).start()

    def fetch_openapi_spec(self, url):
        """Fetches and validates OpenAPI specification"""
        try:
            req = urllib2.Request(url)
            response = urllib2.urlopen(req)
            content = response.read()

            try:
                spec = json.loads(content)
                if not any(key in spec for key in ["swagger", "openapi"]):
                    self._scanner_output.setText(
                        "Invalid OpenAPI specification: Missing version identifier"
                    )
                    return None
                return spec
            except ValueError:
                self._scanner_output.setText(
                    "Invalid OpenAPI specification: Not valid JSON"
                )
                return None

        except Exception as e:
            self._scanner_output.setText("Error fetching OpenAPI spec: %s" % str(e))
            return None

    def analyze_url(self, url):
        """Analyzes a URL for security assessment"""
        try:
            if not re.match(r"^https?://", url):
                url = "http://" + url

            req = urllib2.Request(url)
            response = urllib2.urlopen(req)

            # Gather information about the target
            headers = dict(response.info().items())
            content = response.read()

            security_info = {
                "url": url,
                "status_code": response.getcode(),
                "headers": headers,
                "server_info": headers.get("server", "Unknown"),
                "security_headers": {
                    "x-frame-options": headers.get("x-frame-options", "Not Set"),
                    "content-security-policy": headers.get(
                        "content-security-policy", "Not Set"
                    ),
                    "strict-transport-security": headers.get(
                        "strict-transport-security", "Not Set"
                    ),
                    "x-xss-protection": headers.get("x-xss-protection", "Not Set"),
                    "x-content-type-options": headers.get(
                        "x-content-type-options", "Not Set"
                    ),
                },
                "response_size": len(content),
            }

            return security_info

        except Exception as e:
            self._scanner_output.setText("Error analyzing URL: {str(e)}")
            return None

    def load_prompt_template(self, is_openapi=False):
        """Load the appropriate prompt template"""
        try:
            prompt_file = OPENAPI_PROMPT if is_openapi else SCANNER_PROMPT
            if os.path.exists(prompt_file):
                with open(prompt_file, "r") as f:
                    content = f.read().strip()
                    # Track the last loaded content separately for each type
                    if is_openapi:
                        if content != self._last_openapi_content:
                            self._callbacks.printOutput(
                                "Loaded OpenAPI prompt template"
                            )
                            self._last_openapi_content = content
                    else:
                        if content != self._last_prompt_content:
                            self._callbacks.printOutput(
                                "Loaded scanner prompt template"
                            )
                            self._last_prompt_content = content
                    return content
            else:
                if not hasattr(self, "_prompt_missing_logged"):
                    self._callbacks.printOutput("Prompt file not found: {prompt_file}")
                    self._prompt_missing_logged = True
                return (
                    "Analyze this target for security issues:"
                    if not is_openapi
                    else "Analyze this OpenAPI specification for security vulnerabilities:"
                )
        except Exception as e:
            self._callbacks.printOutput("Error loading prompt: {str(e)}")
            return "Analyze for security vulnerabilities:"

    def get_config_status(self):
        """Get formatted configuration status"""
        config_name = (
            os.path.basename(self.config.get("config_file", "No config"))
            if self.config
            else "No config loaded"
        )
        model_name = self.config.get("model", "Not set") if self.config else "No model"
        api_type = self.config.get("api_type", "Not set") if self.config else "No API"

        return "Configuration: %s | Model: %s | API: %s" % (
            config_name,
            model_name,
            api_type,
        )

    def refresh_prompt_template(self):
        """Refresh the prompt template when config changes"""
        if hasattr(self, "_custom_prompt"):
            initial_prompt = self.load_prompt_template(self.openapi_radio.isSelected())
            if initial_prompt:
                self._custom_prompt.setText(initial_prompt)
                if self.openapi_radio.isSelected():
                    self._last_openapi_content = initial_prompt
                else:
                    self._last_prompt_content = initial_prompt

    def update_config_display(self):
        """Update the configuration display and refresh prompt"""
        if hasattr(self, "config_label"):
            self.config_label.setText(self.get_config_status())
            self.refresh_prompt_template()
