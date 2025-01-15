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
from java.awt import BorderLayout, FlowLayout
from threading import Thread
import json
import urllib2
import re


class BurpferenceScanner:
    def __init__(self, callbacks, helpers, config, api_adapter, colors=None):
        self._callbacks = callbacks
        self._helpers = helpers
        self.config = config
        self.api_adapter = api_adapter

        # Print debug info during initialization
        callbacks.printOutput("Scanner initialized with:")
        callbacks.printOutput("Config: %s" % str(config))
        callbacks.printOutput("API Adapter: %s" % str(api_adapter))

        # Store theme colors
        self.colors = colors or {}
        self.DARK_BACKGROUND = self.colors.get("DARK_BACKGROUND")
        self.LIGHTER_BACKGROUND = self.colors.get("LIGHTER_BACKGROUND")
        self.DREADNODE_GREY = self.colors.get("DREADNODE_GREY")
        self.DREADNODE_ORANGE = self.colors.get("DREADNODE_ORANGE")

    def create_scanner_tab(self):
        """Creates the security analysis scanner tab"""
        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        panel.setBackground(self.DARK_BACKGROUND)

        # Target input section
        target_panel = JPanel(FlowLayout(FlowLayout.LEFT))
        target_panel.setBackground(self.DARK_BACKGROUND)

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

        # Custom prompt panel
        prompt_panel = JPanel()
        prompt_panel.setBackground(self.DARK_BACKGROUND)
        prompt_label = JLabel("Custom Analysis Instructions:")
        prompt_label.setForeground(self.DREADNODE_GREY)
        self._custom_prompt = JTextArea(5, 50)
        self._custom_prompt.setLineWrap(True)
        self._custom_prompt.setWrapStyleWord(True)
        self._custom_prompt.setBackground(self.LIGHTER_BACKGROUND)
        self._custom_prompt.setForeground(self.DREADNODE_ORANGE)
        prompt_scroll = JScrollPane(self._custom_prompt)

        # Analyze button
        scan_button = JButton(
            "Start Security Analysis", actionPerformed=self.analyze_target
        )
        scan_button.setBackground(self.DREADNODE_ORANGE)
        scan_button.setForeground(self.DREADNODE_GREY)

        # Results area
        self._scanner_output = JTextArea(20, 50)
        self._scanner_output.setEditable(False)
        self._scanner_output.setLineWrap(True)
        self._scanner_output.setWrapStyleWord(True)
        self._scanner_output.setBackground(self.LIGHTER_BACKGROUND)
        self._scanner_output.setForeground(self.DREADNODE_ORANGE)
        scanner_scroll = JScrollPane(self._scanner_output)

        # Layout components
        panel.add(target_panel)
        panel.add(prompt_panel)
        panel.add(prompt_scroll)
        panel.add(scan_button)
        panel.add(scanner_scroll)

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
                        custom_prompt
                        if custom_prompt
                        else "Analyze this URL for potential security vulnerabilities, common web security issues, and misconfigurations:"
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
