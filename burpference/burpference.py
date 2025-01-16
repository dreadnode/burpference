# -*- coding: utf-8 -*-
# type: ignore[import]
from datetime import datetime
from burp import IBurpExtender, ITab, IHttpListener, IScanIssue
from java.awt import BorderLayout, GridBagLayout, GridBagConstraints, Font, Dimension
from javax.swing import (
    JPanel, JTextArea, JScrollPane,
    BorderFactory, JSplitPane, JButton, JComboBox,
    JTable, table, ListSelectionModel, JOptionPane, JTextField, JTabbedPane)
from javax.swing import BoxLayout, JLabel
from javax.swing.table import DefaultTableCellRenderer, TableRowSorter
from javax.swing.border import TitledBorder
from java.util import Comparator
import json
import urllib2
import os
from consts import *
from api_adapters import get_api_adapter
from issues import BurpferenceIssue
from threading import Thread
from scanner import BurpferenceScanner


def load_ascii_art(file_path):
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except IOError:
        return "Failed to load ASCII art"


SQUID_ASCII = load_ascii_art(SQUID_ASCII_FILE)


class BurpExtender(IBurpExtender, ITab, IHttpListener):

    def __init__(self):
        self.popupShown = False
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        try:
            if not os.path.exists(LOG_DIR):
                os.makedirs(LOG_DIR, 0755)
        except OSError as e:
            print("Failed to create log directory: %s" % str(e))

        self.log_file_path = os.path.join(
            LOG_DIR,
            "burpference_log_{}.txt".format(timestamp)
        )
        self.config = None
        self.api_adapter = None
        self.is_running = True
        self.logArea = None
        self.temp_log_messages = []
        self.request_counter = 0
        self.log_message("Extension initialized and running.")
        self._hosts = set()
        self.scanner = None  # Will initialize after callbacks

    def registerExtenderCallbacks(self, callbacks):
        self._callbacks = callbacks
        self._helpers = callbacks.getHelpers()
        callbacks.setExtensionName("burpference")

        # Create main panel
        self._panel = JPanel(BorderLayout())
        self._panel.setBackground(DARK_BACKGROUND)

        # Create input panel
        inputPanel = JPanel(GridBagLayout())
        inputPanel.setBackground(DARK_BACKGROUND)

        outerBorder = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "burpference, made with <3 by @dreadnode"
        )
        outerBorder.setTitleColor(DREADNODE_PURPLE)
        outerBorder.setTitleFont(Font(Font.SANS_SERIF, Font.BOLD, 12))

        inputPanel.setBorder(outerBorder)

        c = GridBagConstraints()
        c.fill = GridBagConstraints.HORIZONTAL
        c.weightx = 1
        c.gridx = 0
        c.gridy = 0

        # Load configuration files dynamically from directory
        self.configFiles = self.loadConfigFiles()
        self.configSelector = JComboBox(self.configFiles)
        self.configSelector.setBackground(LIGHTER_BACKGROUND)
        self.configSelector.setForeground(DREADNODE_GREY)
        self.configSelector.addActionListener(self.loadConfiguration)
        c.gridy += 1
        inputPanel.add(self.configSelector, c)

        # stopButton
        c.gridy += 1
        self.stopButton = JButton("Stop Extension")
        self.stopButton.setBackground(DREADNODE_ORANGE)
        self.stopButton.setForeground(DREADNODE_GREY)
        self.stopButton.addActionListener(self.stopExtension)
        inputPanel.add(self.stopButton, c)

        # Log area
        self.logArea = JTextArea(10, 30)
        self.logArea.setEditable(False)
        self.logArea.setBackground(LIGHTER_BACKGROUND)
        self.logArea.setForeground(DREADNODE_GREY)
        self.logArea.setCaretColor(DREADNODE_GREY)
        logScrollPane = JScrollPane(self.logArea)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Extension Log Output"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        boldFont = border.getTitleFont().deriveFont(Font.BOLD, 14)
        border.setTitleFont(boldFont)
        logScrollPane.setBorder(border)

        # Add any temporary log messages
        for log_entry in self.temp_log_messages:
            self.logArea.append(log_entry)
        self.temp_log_messages = []

        # Create a split pane for input and log
        splitPane = JSplitPane(JSplitPane.VERTICAL_SPLIT,
                               inputPanel, logScrollPane)
        splitPane.setBackground(DARK_BACKGROUND)
        splitPane.setDividerSize(0)
        splitPane.setEnabled(False)
        splitPane.setResizeWeight(0.1)

        # Create HTTP history table
        self.historyTable = JTable()
        self.historyTable.setBackground(LIGHTER_BACKGROUND)
        self.historyTable.setForeground(DREADNODE_GREY)
        self.historyTable.setSelectionBackground(DREADNODE_ORANGE)
        self.historyTable.setSelectionForeground(DREADNODE_GREY)
        self.historyTable.setGridColor(DREADNODE_GREY)
        self.historyTableModel = table.DefaultTableModel(
            ["#", "Timestamp", "Host", "URL", "Request", "Response"], 0)
        self.historyTable.setModel(self.historyTableModel)

        class NumericComparator(Comparator):
            def compare(self, s1, s2):
                # Convert strings to integers for comparison
                try:
                    n1 = int(s1)
                    n2 = int(s2)
                    return n1 - n2
                except:
                    return 0

        # Add sorting capability
        sorter = TableRowSorter(self.historyTableModel)
        self.historyTable.setRowSorter(sorter)

        # Set the numeric comparator for the ID column
        sorter.setComparator(0, NumericComparator())

        # Set selection mode and listener
        self.historyTable.setSelectionMode(ListSelectionModel.SINGLE_SELECTION)
        self.historyTable.getSelectionModel().addListSelectionListener(
            self.historyTableSelectionChanged)
        historyScrollPane = JScrollPane(self.historyTable)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "HTTP History"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        boldFont = border.getTitleFont().deriveFont(Font.BOLD, 14)
        border.setTitleFont(boldFont)
        historyScrollPane.setBorder(border)

        # Create request and response areas
        self.requestArea = JTextArea(10, 30)
        self.requestArea.setEditable(False)
        self.requestArea.setLineWrap(True)
        self.requestArea.setWrapStyleWord(True)
        self.requestArea.setBackground(LIGHTER_BACKGROUND)
        self.requestArea.setForeground(DREADNODE_ORANGE)
        self.requestArea.setCaretColor(DREADNODE_GREY)
        requestScrollPane = JScrollPane(self.requestArea)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Inference Request - Live View"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        boldFont = border.getTitleFont().deriveFont(Font.BOLD, 14)
        border.setTitleFont(boldFont)
        requestScrollPane.setBorder(border)

        self.responseArea = JTextArea(10, 30)
        self.responseArea.setEditable(False)
        self.responseArea.setLineWrap(True)
        self.responseArea.setWrapStyleWord(True)
        self.responseArea.setBackground(LIGHTER_BACKGROUND)
        self.responseArea.setForeground(DREADNODE_ORANGE)
        self.responseArea.setCaretColor(DREADNODE_GREY)
        responseScrollPane = JScrollPane(self.responseArea)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Inference Response - Live View"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        boldFont = border.getTitleFont().deriveFont(Font.BOLD, 14)
        border.setTitleFont(boldFont)
        responseScrollPane.setBorder(border)

        # Create split panes
        diffSplitPane = JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT, requestScrollPane, responseScrollPane)
        diffSplitPane.setBackground(DARK_BACKGROUND)
        diffSplitPane.setDividerSize(2)
        diffSplitPane.setResizeWeight(0.5)

        # Selected request/response areas
        self.selectedRequestArea = JTextArea(10, 30)
        self.selectedRequestArea.setEditable(False)
        self.selectedRequestArea.setLineWrap(True)
        self.selectedRequestArea.setWrapStyleWord(True)
        self.selectedRequestArea.setBackground(LIGHTER_BACKGROUND)
        self.selectedRequestArea.setForeground(DREADNODE_ORANGE)
        self.selectedRequestArea.setCaretColor(DREADNODE_GREY)
        selectedRequestScrollPane = JScrollPane(self.selectedRequestArea)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Selected HTTP Request & Response"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        boldFont = border.getTitleFont().deriveFont(Font.BOLD, 14)
        border.setTitleFont(boldFont)
        selectedRequestScrollPane.setBorder(border)

        self.selectedResponseArea = JTextArea(10, 30)
        self.selectedResponseArea.setEditable(False)
        self.selectedResponseArea.setLineWrap(True)
        self.selectedResponseArea.setWrapStyleWord(True)
        self.selectedResponseArea.setBackground(LIGHTER_BACKGROUND)
        self.selectedResponseArea.setForeground(DREADNODE_ORANGE)
        self.selectedResponseArea.setCaretColor(DREADNODE_GREY)
        selectedResponseScrollPane = JScrollPane(self.selectedResponseArea)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Selected Inference Response"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        boldFont = border.getTitleFont().deriveFont(Font.BOLD, 14)
        border.setTitleFont(boldFont)
        selectedResponseScrollPane.setBorder(border)

        selectedDiffSplitPane = JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT, selectedRequestScrollPane,     selectedResponseScrollPane)
        selectedDiffSplitPane.setBackground(DARK_BACKGROUND)
        selectedDiffSplitPane.setDividerSize(2)
        selectedDiffSplitPane.setResizeWeight(0.5)

        # Main split pane for history and selected entry
        mainSplitPane = JSplitPane(
            JSplitPane.VERTICAL_SPLIT, historyScrollPane, selectedDiffSplitPane)
        mainSplitPane.setBackground(DARK_BACKGROUND)
        mainSplitPane.setDividerSize(2)
        mainSplitPane.setResizeWeight(0.5)

        # Add components to main panel
        self._panel.add(mainSplitPane, BorderLayout.CENTER)
        self._panel.add(splitPane, BorderLayout.SOUTH)
        self._panel.add(diffSplitPane, BorderLayout.NORTH)

        self.inference_tab = self.create_inference_logger_tab()
        self.scanner_tab = self.create_scanner_tab()

        self.tabbedPane = JTabbedPane()
        self.tabbedPane.setBackground(DARK_BACKGROUND)
        self.tabbedPane.setForeground(DREADNODE_GREY)
        self.tabbedPane.addTab("burpference", self._panel)
        self.tabbedPane.addTab("Inference Logger", self.inference_tab)

        # Initialize scanner AFTER loading config
        self.scanner = None

        # Now initialize scanner with current config
        colors = {
            'DARK_BACKGROUND': DARK_BACKGROUND,
            'LIGHTER_BACKGROUND': LIGHTER_BACKGROUND,
            'DREADNODE_GREY': DREADNODE_GREY,
            'DREADNODE_ORANGE': DREADNODE_ORANGE
        }
        self.scanner = BurpferenceScanner(
            callbacks=self._callbacks,
            helpers=self._helpers,
            config=None,
            api_adapter=None,
            colors=colors
        )

        self.scanner_tab = self.scanner.create_scanner_tab()
        self.tabbedPane.addTab("Scanner", self.scanner_tab)

        for i in range(self.tabbedPane.getTabCount()):
            self.tabbedPane.setBackgroundAt(i, DREADNODE_GREY)
            self.tabbedPane.setForegroundAt(i, DREADNODE_ORANGE)

        # Register with Burp
        callbacks.customizeUiComponent(self.tabbedPane)
        callbacks.addSuiteTab(self)
        callbacks.registerHttpListener(self)

        # Initialize
        self.is_running = True
        self.updateUIState()
        self.log_message("Extension initialized and running.")

        callbacks.printOutput(SQUID_ASCII + "\n\n")
        callbacks.printOutput(
            "Yer configs be stowed and ready from " + CONFIG_DIR)
        callbacks.printOutput(
            "\nNow ye be speakin' the pirate's tongue, savvy?")

        self.promptForConfiguration()
        self.applyDarkTheme(self.tabbedPane)

    def getTabCaption(self):
        return "burpference"

    def getUiComponent(self):
        return self.tabbedPane

    def stopExtension(self, event):
        if self.is_running:
            self.is_running = False
            self._callbacks.removeHttpListener(
                self)
            self.log_message(
                "Extension stopped. No further traffic will be processed.")
            self.updateUIState()

    def updateUIState(self):
        if self.is_running:
            self.stopButton.setText("Stop Extension")
            for listener in self.stopButton.getActionListeners():
                self.stopButton.removeActionListener(listener)
            self.stopButton.addActionListener(self.stopExtension)
        else:
            self.stopButton.setText(
                "Extension Stopped - Unload and reload if required, doing so will remove displayed logs and state")
            for listener in self.stopButton.getActionListeners():
                self.stopButton.removeActionListener(listener)

    def loadConfigFiles(self):
        if not os.path.exists(CONFIG_DIR):
            self.log_message("Config directory not found: {CONFIG_DIR}")
            return []
        return [f for f in os.listdir(CONFIG_DIR) if f.endswith('.json')]

    def loadConfiguration(self, event):
        selected_config = self.configSelector.getSelectedItem()
        config_path = os.path.join(CONFIG_DIR, selected_config)
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as config_file:
                    self.config = json.load(config_file)
                    self.config["config_file"] = selected_config

                try:
                    self.api_adapter = get_api_adapter(self.config)
                    if self.scanner:
                        self.scanner.config = self.config
                        self.scanner.api_adapter = self.api_adapter
                        self.scanner.update_config_display()
                    self.log_message("API adapter initialized successfully")
                except ValueError as e:
                    self.log_message("Error initializing API adapter: %s" % str(e))
                    self.api_adapter = None
                    if self.scanner:
                        self.scanner.api_adapter = None
                except Exception as e:
                    self.log_message(
                        "Unexpected error initializing API adapter: %s" % str(e))
                    self.api_adapter = None
                    if self.scanner:
                        self.scanner.api_adapter = None
            except ValueError as e:
                self.log_message(
                    "Error parsing JSON in configuration file: %s" % str(e))
                self.config = None
                self.api_adapter = None
                if self.scanner:
                    self.scanner.config = None
                    self.scanner.api_adapter = None
            except Exception as e:
                self.log_message(
                    "Unexpected error loading configuration: %s" % str(e))
                self.config = None
                self.api_adapter = None
                if self.scanner:
                    self.scanner.config = None
                    self.scanner.api_adapter = None
        else:
            self.log_message(
                "Configuration file %s not found." % selected_config)
            self.config = None
            self.api_adapter = None
            if self.scanner:
                self.scanner.config = None
                self.scanner.api_adapter = None

    def create_inference_logger_tab(self):
        panel = JPanel(BorderLayout())
        panel.setBackground(DARK_BACKGROUND)

        self.inferenceLogTable = JTable()
        self.inferenceLogTable.setBackground(LIGHTER_BACKGROUND)
        self.inferenceLogTable.setForeground(DREADNODE_GREY)
        self.inferenceLogTable.setSelectionBackground(DREADNODE_PURPLE)
        self.inferenceLogTable.setSelectionForeground(DREADNODE_GREY)
        self.inferenceLogTable.setGridColor(DREADNODE_GREY)

        self.inferenceLogTableModel = table.DefaultTableModel(
            ["Timestamp", "API Endpoint", "Proxy Request", "Model Response", "Status"], 0)
        self.inferenceLogTable.setModel(self.inferenceLogTableModel)
        self.inferenceLogTable.setSelectionMode(
            ListSelectionModel.SINGLE_SELECTION)

        self.inferenceLogTable.getSelectionModel().addListSelectionListener(
            self.inferenceLogSelectionChanged)

        inferenceLogScrollPane = JScrollPane(self.inferenceLogTable)
        border = BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "API Requests Log"
        )
        border.setTitleColor(DREADNODE_ORANGE)
        border.setTitleFont(border.getTitleFont().deriveFont(Font.BOLD, 14))
        inferenceLogScrollPane.setBorder(border)

        self.inferenceRequestDetail = JTextArea(10, 30)
        self.inferenceRequestDetail.setEditable(False)
        self.inferenceRequestDetail.setLineWrap(True)
        self.inferenceRequestDetail.setWrapStyleWord(True)
        self.inferenceRequestDetail.setBackground(LIGHTER_BACKGROUND)
        self.inferenceRequestDetail.setForeground(DREADNODE_ORANGE)
        requestDetailPane = JScrollPane(self.inferenceRequestDetail)
        requestDetailPane.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Inference Request Detail"
        ))

        self.inferenceResponseDetail = JTextArea(10, 30)
        self.inferenceResponseDetail.setEditable(False)
        self.inferenceResponseDetail.setLineWrap(True)
        self.inferenceResponseDetail.setWrapStyleWord(True)
        self.inferenceResponseDetail.setBackground(LIGHTER_BACKGROUND)
        self.inferenceResponseDetail.setForeground(DREADNODE_ORANGE)
        responseDetailPane = JScrollPane(self.inferenceResponseDetail)
        responseDetailPane.setBorder(BorderFactory.createTitledBorder(
            BorderFactory.createLineBorder(DREADNODE_ORANGE),
            "Inference Response Detail"
        ))

        # Create split pane for details
        detailsSplitPane = JSplitPane(
            JSplitPane.HORIZONTAL_SPLIT,
            requestDetailPane,
            responseDetailPane
        )
        detailsSplitPane.setResizeWeight(0.5)

        # Create main split pane
        mainSplitPane = JSplitPane(
            JSplitPane.VERTICAL_SPLIT,
            inferenceLogScrollPane,
            detailsSplitPane
        )
        mainSplitPane.setResizeWeight(0.5)

        panel.add(mainSplitPane, BorderLayout.CENTER)

        return panel

    def create_scanner_tab(self):
        """Creates the burpference scanner tab with domain filtering and direct model interaction"""
        panel = JPanel()
        panel.setLayout(BoxLayout(panel, BoxLayout.Y_AXIS))
        panel.setBackground(DARK_BACKGROUND)

        # Create top control panel
        top_panel = JPanel()
        top_panel.setLayout(BoxLayout(top_panel, BoxLayout.X_AXIS))
        top_panel.setBackground(DARK_BACKGROUND)

        # Domain selector
        domain_panel = JPanel()
        domain_panel.setBackground(DARK_BACKGROUND)
        domain_label = JLabel("Target Domain:")
        domain_label.setForeground(DREADNODE_GREY)
        self._domain_selector = JComboBox(list(self._hosts))
        self._domain_selector.setBackground(LIGHTER_BACKGROUND)
        self._domain_selector.setForeground(DREADNODE_GREY)
        domain_panel.add(domain_label)
        domain_panel.add(self._domain_selector)
        top_panel.add(domain_panel)

        # Optional prompt input
        middle_panel = JPanel()
        middle_panel.setBackground(DARK_BACKGROUND)
        middle_panel.setLayout(BoxLayout(middle_panel, BoxLayout.Y_AXIS))
        prompt_label = JLabel("Custom Analysis Prompt:")
        prompt_label.setForeground(DREADNODE_GREY)
        self._custom_prompt = JTextArea(5, 50)
        self._custom_prompt.setLineWrap(True)
        self._custom_prompt.setWrapStyleWord(True)
        self._custom_prompt.setBackground(LIGHTER_BACKGROUND)
        self._custom_prompt.setForeground(DREADNODE_ORANGE)
        prompt_scroll = JScrollPane(self._custom_prompt)

        # Analyze button
        analyze_button = JButton("Analyze Domain", actionPerformed=self.analyze_domain)
        analyze_button.setBackground(DREADNODE_ORANGE)
        analyze_button.setForeground(DREADNODE_GREY)

        middle_panel.add(prompt_label)
        middle_panel.add(prompt_scroll)
        middle_panel.add(analyze_button)

        # Results area
        self._scanner_output = JTextArea(20, 50)
        self._scanner_output.setEditable(False)
        self._scanner_output.setLineWrap(True)
        self._scanner_output.setWrapStyleWord(True)
        self._scanner_output.setBackground(LIGHTER_BACKGROUND)
        self._scanner_output.setForeground(DREADNODE_ORANGE)
        scanner_scroll = JScrollPane(self._scanner_output)

        # Add all components
        panel.add(top_panel)
        panel.add(middle_panel)
        panel.add(scanner_scroll)

        return panel

    def analyze_domain(self, event):
        """Handles the domain analysis button click"""
        domain = self._domain_selector.getSelectedItem()
        custom_prompt = self._custom_prompt.getText()

        def run_analysis():
            self._scanner_output.setText("Analyzing domain: %s...\n" % domain)
            try:
                # Get all requests for selected domain
                http_pairs = self.get_domain_traffic(domain)
                if not http_pairs:
                    self._scanner_output.append("\nNo traffic found for domain.")
                    return

                # Use custom prompt if provided, otherwise use default
                prompt = custom_prompt if custom_prompt else "Analyze this domain's traffic for security issues:"

                # Prepare and send to current model
                analysis_request = self.api_adapter.prepare_request(
                    user_content=json.dumps(http_pairs, indent=2),
                    system_content=prompt
                )

                # Make request and process response
                req = urllib2.Request(self.config.get("host", ""))
                for header, value in self.config.get("headers", {}).items():
                    req.add_header(header, value)

                response = urllib2.urlopen(req, json.dumps(analysis_request))
                response_data = response.read()
                analysis = self.api_adapter.process_response(response_data)

                # Update UI
                self._scanner_output.setText("Analysis for %s:\n\n%s" % (domain, analysis))

            except Exception as e:
                self._scanner_output.setText("Error analyzing domain: %s" % str(e))

        # Run analysis in background thread
        Thread(target=run_analysis).start()

    def get_domain_traffic(self, domain):
        """Gets all traffic for a specific domain"""
        traffic = []
        for message in self._callbacks.getProxyHistory():
            if domain in message.getHttpService().getHost():
                analyzed_request = self._helpers.analyzeRequest(message)
                analyzed_response = self._helpers.analyzeResponse(message.getResponse())

                # Extract request/response data
                request_info = {
                    "method": analyzed_request.getMethod(),
                    "url": str(message.getUrl()),
                    "headers": dict(header.split(': ', 1) for header in analyzed_request.getHeaders()[1:] if ': ' in header),
                    "body": message.getRequest()[analyzed_request.getBodyOffset():].tostring()
                }

                response_info = {
                    "status": analyzed_response.getStatusCode(),
                    "headers": dict(header.split(': ', 1) for header in analyzed_response.getHeaders()[1:] if ': ' in header),
                    "body": message.getResponse()[analyzed_response.getBodyOffset():].tostring()
                }

                traffic.append({"request": request_info, "response": response_info})
        return traffic

    def inferenceLogSelectionChanged(self, event):
        selectedRow = self.inferenceLogTable.getSelectedRow()
        if selectedRow != -1:
            try:
                # Get the request and response data from columns
                request = self.inferenceLogTableModel.getValueAt(selectedRow, 2)  # Proxy Request column
                response = self.inferenceLogTableModel.getValueAt(selectedRow, 3)  # Model Response column

                # Format the request JSON
                try:
                    if isinstance(request, dict):
                        formatted_request = json.dumps(request, indent=2)
                    else:
                        formatted_request = json.dumps(json.loads(request), indent=2)
                except (ValueError, TypeError):
                    formatted_request = str(request)

                try:
                    if isinstance(response, dict):
                        response_obj = response
                    else:
                        response_obj = json.loads(response)

                    if isinstance(response_obj, dict) and 'message' in response_obj and 'content' in response_obj['message']:
                        # Get just the content string and handle unicode
                        content = response_obj['message']['content']
                        # Handle unicode strings and newlines
                        formatted_response = content.replace('\\n', '\n')
                    else:
                        formatted_response = json.dumps(response_obj, indent=2)
                except (ValueError, AttributeError, TypeError):
                    formatted_response = str(response)

                self.inferenceRequestDetail.setText(formatted_request)
                self.inferenceResponseDetail.setText(formatted_response)

                self.inferenceRequestDetail.setCaretPosition(0)
                self.inferenceResponseDetail.setCaretPosition(0)

            except Exception as e:
                self.log_message("Error updating inference details: %s" % str(e))

    def historyTableSelectionChanged(self, event):
        selectedRow = self.historyTable.getSelectedRow()
        if selectedRow != -1:
            try:
                # Get the stored HTTP pair and model analysis
                http_pair_json = self.historyTableModel.getValueAt(selectedRow, 4)
                model_analysis = self.historyTableModel.getValueAt(selectedRow, 5)

                try:
                    # Parse and show the HTTP pair
                    http_pair = json.loads(http_pair_json)
                    self.selectedRequestArea.setText(json.dumps(http_pair, indent=2))

                    model_text = model_analysis.strip('"').decode('unicode_escape')
                    model_text = model_text.replace('\\n', '\n')
                    self.selectedResponseArea.setText(model_text)

                    self.selectedRequestArea.setCaretPosition(0)
                    self.selectedResponseArea.setCaretPosition(0)
                except Exception as e:
                    self.log_message("Error parsing stored data: %s" % str(e))
                    self.selectedRequestArea.setText(http_pair_json)
                    self.selectedResponseArea.setText(model_analysis)

            except Exception as e:
                self.log_message("Error updating history details: %s" % str(e))

    def colorizeHistoryTable(self):
        renderer = self.SeverityCellRenderer()
        for column in range(self.historyTable.getColumnCount()):
            self.historyTable.getColumnModel().getColumn(column).setCellRenderer(renderer)

    class SeverityCellRenderer(DefaultTableCellRenderer):
        def getTableCellRendererComponent(self, table, value, isSelected, hasFocus, row, column):
            component = super(BurpExtender.SeverityCellRenderer, self).getTableCellRendererComponent(
                table, value, isSelected, hasFocus, row, column)

            component.setForeground(DREADNODE_GREY)

            try:
                response = str(table.getModel().getValueAt(row, 5))

                if "**CRITICAL**" in response:
                    component.setBackground(CRITICAL_COLOR)
                    component.setForeground(Color.WHITE)
                elif "**HIGH**" in response:
                    component.setBackground(HIGH_COLOR)
                    component.setForeground(Color.WHITE)
                elif "**MEDIUM**" in response:
                    component.setBackground(MEDIUM_COLOR)
                    component.setForeground(Color.BLACK)
                elif "**LOW**" in response:
                    component.setBackground(LOW_COLOR)
                    component.setForeground(Color.BLACK)
                elif "**INFORMATIONAL**" in response:
                    component.setBackground(INFORMATIONAL_COLOR)
                    component.setForeground(Color.BLACK)
                else:
                    component.setBackground(LIGHTER_BACKGROUND)
                    component.setForeground(DREADNODE_GREY)

                if isSelected:
                    component.setBackground(DREADNODE_ORANGE)
                    component.setForeground(DREADNODE_GREY)

            except Exception as e:
                component.setBackground(LIGHTER_BACKGROUND)
                component.setForeground(DREADNODE_GREY)

            component.setOpaque(True)
            return component

    def log_message(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = "[{0}] {1}\n".format(timestamp, message)

        if self.logArea is None:
            self.temp_log_messages.append(log_entry)
        else:
            self.logArea.append(log_entry)
            self.logArea.setCaretPosition(
                self.logArea.getDocument().getLength())

        try:
            log_dir = os.path.dirname(self.log_file_path)
            if not os.path.exists(log_dir):
                os.makedirs(log_dir, 0755)

            with open(self.log_file_path, 'a+') as log_file:
                log_file.write(log_entry)
        except (IOError, OSError) as e:
            print("Warning: Could not write to log file: %s" % str(e))

    def applyDarkTheme(self, component):
        if isinstance(component, JPanel) or isinstance(component, JScrollPane):
            component.setBackground(DARK_BACKGROUND)
            border = component.getBorder()
            if isinstance(border, TitledBorder):
                border.setTitleColor(DREADNODE_ORANGE)
                boldFont = Font(Font.SANS_SERIF, Font.BOLD, 14)
                border.setTitleFont(boldFont)

        component.setForeground(DREADNODE_GREY)

        if isinstance(component, JTextArea) or isinstance(component, JTextField):
            component.setCaretColor(DREADNODE_GREY)
            component.setBackground(LIGHTER_BACKGROUND)
            component.setForeground(DREADNODE_ORANGE)

        if isinstance(component, JSplitPane):
            component.setBackground(DARK_BACKGROUND)
            component.setForeground(DREADNODE_GREY)
            component.setDividerSize(2)
            component.setDividerLocation(0.5)

        if hasattr(component, 'getComponents'):
            for child in component.getComponents():
                self.applyDarkTheme(child)

    def map_severity(self, ai_severity):
        """Map burpference model severity levels to Burp's iscan exact severity strings"""
        severity_map = {
            "CRITICAL": "High",
            "HIGH": "High",
            "MEDIUM": "Medium",
            "LOW": "Low",
            "INFORMATIONAL": "Information"
        }
        return severity_map.get(ai_severity, "Information")

    def extract_severity_from_response(self, response):
        """Extract severity level from model response"""
        for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]:
            if "**%s**" % level in response:
                return level
        return "INFORMATIONAL"

    def create_scan_issue(self, messageInfo, processed_response):
        try:
            severity = self.extract_severity_from_response(processed_response)
            burp_severity = self.map_severity(severity)

            # Convert response to string and handle escaping
            if isinstance(processed_response, str):
                detail = processed_response
            else:
                detail = str(processed_response)

            if detail.startswith('"') and detail.endswith('"'):
                detail = detail[1:-1]

            # Create properly formatted issue name
            issue_name = "burpference: %s Security Finding" % severity

            issue = BurpferenceIssue(
                httpService=messageInfo.getHttpService(),
                url=self._helpers.analyzeRequest(messageInfo).getUrl(),
                httpMessages=[messageInfo],
                name=issue_name,
                detail=detail,
                severity=burp_severity,
                confidence="Certain"
            )

            self._callbacks.addScanIssue(issue)
            self.log_message("Added %s issue to Burp Scanner" % severity)

        except Exception as e:
            self.log_message("Error creating scan issue: %s" % str(e))

    def processHttpMessage(self, toolFlag, messageIsRequest, messageInfo):
        if messageIsRequest:
            # Add new domains to both main extension and scanner
            host = messageInfo.getHttpService().getHost()
            if host not in self._hosts:
                self._hosts.add(host)
                if self.scanner:
                    self.scanner.add_host(host)
        if not self.is_running:
            return
        if not self.api_adapter:
            if not hasattr(self, '_no_adapter_logged'):
                self.log_message("No API adapter configured. Please select a configuration file.")
                self._no_adapter_logged = True
            return
        if messageIsRequest:
            # Store the request for later use
            self.current_request = messageInfo
            host = messageInfo.getHttpService().getHost()
            if host not in self._hosts:
                self._hosts.add(host)
                if hasattr(self, '_domain_selector'):
                    self._domain_selector.addItem(host)
            if self.scanner:
                self.scanner.add_host(host)
        else:
            request = self.current_request
            response = messageInfo

            # Filter MIME content types to reduce noise and exceeding tokens
            responseInfo = self._helpers.analyzeResponse(
                response.getResponse())
            contentType = responseInfo.getStatedMimeType().lower()
            if contentType in ['css', 'image', 'script', 'video', 'audio', 'font']:
                return

            # Filter request size
            if len(request.getRequest()) > MAX_REQUEST_SIZE:
                return
            try:
                analyzed_request = self._helpers.analyzeRequest(request)
                analyzed_response = self._helpers.analyzeResponse(response.getResponse())

                # Get the body bytes
                request_body = request.getRequest()[analyzed_request.getBodyOffset():]
                response_body = response.getResponse()[analyzed_response.getBodyOffset():]

                # Try to safely decode bodies, fallback to hex for binary data
                try:
                    request_body_str = request_body.tostring().decode('utf-8')
                except UnicodeDecodeError:
                    request_body_str = "<binary data length: %d>" % len(request_body)

                try:
                    response_body_str = response_body.tostring().decode('utf-8')
                except UnicodeDecodeError:
                    response_body_str = "<binary data length: %d>" % len(response_body)

                self.request_counter += 1

                # Table display data
                table_metadata = {
                    "id": str(self.request_counter),
                    "host": request.getHttpService().getHost(),
                    "url": str(request.getUrl()),
                }

                # Data for model analysis
                request_data = {
                    "method": analyzed_request.getMethod(),
                    "url": str(request.getUrl()),
                    "headers": dict(header.split(': ', 1) for header in analyzed_request.getHeaders()[1:] if ': ' in header),
                    "body": request_body_str
                }

                # Package the original HTTP response
                response_data = {
                    "status_code": analyzed_response.getStatusCode(),
                    "headers": dict(header.split(': ', 1) for header in analyzed_response.getHeaders()[1:] if ': ' in header),
                    "body": response_body_str
                }

                # Create the HTTP pair to send to the model
                http_pair = {
                    "request": request_data,
                    "response": response_data
                }

                # Load prompt template for system role
                if os.path.exists(PROXY_PROMPT):
                    with open(PROXY_PROMPT, 'r') as prompt_file:
                        system_content = prompt_file.read().strip()
                    # Only log if there's an issue or if it's different from last time
                    if not hasattr(self, '_last_system_content') or system_content != self._last_system_content:
                        self.log_message("Custom prompt loaded from " + PROXY_PROMPT)
                        self._last_system_content = system_content
                else:
                    if not hasattr(self, '_prompt_missing_logged'):
                        self.log_message("No prompt file found. Using default prompt.")
                        self._prompt_missing_logged = True
                    system_content = "Examine this request and response pair for any security issues:"

                # Prepare the request using the adapter
                remote_request = self.api_adapter.prepare_request(
                    user_content=json.dumps(http_pair, indent=2),
                    system_content=system_content
                )

                # Send request to model
                req = urllib2.Request(self.config.get("host", ""))
                for header, value in self.config.get("headers", {}).items():
                    req.add_header(header, value)

                try:
                    response = urllib2.urlopen(req, json.dumps(remote_request))
                    response_data = response.read()
                    processed_response = self.api_adapter.process_response(response_data)
                    status = "Success"
                except urllib2.HTTPError as e:
                    error_message = e.read().decode('utf-8')
                    error_details = {
                        "status_code": e.code,
                        "headers": dict(e.headers),
                        "body": error_message
                    }
                    processed_response = json.dumps(error_details, indent=2)
                    self.log_message("API Error Response:\nStatus Code: %d\nHeaders: %s\nBody: %s" %
                                     (e.code, dict(e.headers), error_message))
                    status = "Failed (%d)" % e.code
                except Exception as e:
                    processed_response = "Error: %s" % str(e)
                    self.log_message("General Error: %s" % str(e))
                    status = "Failed"

                # Always log to inference logger
                if self.is_running:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.inferenceLogTableModel.addRow([
                        timestamp,
                        self.config.get("host", ""),
                        json.dumps(remote_request),
                        processed_response,
                        status
                    ])

                # Only update the main UI if we got a successful response
                if status == "Success" and self.is_running:
                    # Create Burp scanner issue
                    self.create_scan_issue(messageInfo, processed_response)

                    # Add to history table with metadata
                    self.historyTableModel.addRow([
                        table_metadata.get("id", ""),
                        timestamp,
                        table_metadata.get("host", ""),
                        table_metadata.get("url", ""),
                        json.dumps(http_pair, indent=2),  # Store the HTTP request/response pair
                        json.dumps(processed_response, indent=2)  # Store the model's analysis
                    ])
                    self.colorizeHistoryTable()

                    self.requestArea.append("\n\n=== Request #" + str(self.request_counter) + " ===\n")
                    try:
                        formatted_request = json.dumps(http_pair, indent=2)
                        formatted_request = formatted_request.replace('\\n', '\n')
                        formatted_request = formatted_request.replace('\\"', '"')
                        self.requestArea.append(formatted_request)
                    except Exception as e:
                        self.requestArea.append(str(http_pair))
                    self.requestArea.setCaretPosition(self.requestArea.getDocument().getLength())

                    self.responseArea.append("\n\n=== Response #" + str(self.request_counter) + " ===\n")
                    try:
                        if isinstance(processed_response, dict) and 'message' in processed_response and 'content' in processed_response['message']:
                            formatted_response = processed_response['message']['content']
                        else:
                            formatted_response = json.dumps(processed_response, indent=2)
                        formatted_response = formatted_response.replace('\\n', '\n')
                        formatted_response = formatted_response.replace('\\"', '"')
                        self.responseArea.append(formatted_response)
                    except Exception as e:
                        self.responseArea.append(str(processed_response))
                    self.responseArea.setCaretPosition(self.responseArea.getDocument().getLength())

            except Exception as e:
                self.log_message("Error processing request: %s" % str(e))

    def promptForConfiguration(self):
        JOptionPane.showMessageDialog(
            self._panel,
            "Select a configuration file to load in the burpference extension"
            " tab and go brrr",
            "burpference Configuration Required",
            JOptionPane.INFORMATION_MESSAGE)