from burp import IScanIssue


class BurpferenceIssue(IScanIssue):
    def __init__(
        self, httpService, url, httpMessages, name, detail, severity, confidence
    ):
        self._httpService = httpService
        self._url = url
        self._httpMessages = httpMessages
        self._name = name
        self._detail = detail
        self._severity = severity
        self._confidence = confidence

    def getUrl(self):
        return self._url

    def getIssueName(self):
        return self._name

    def getIssueType(self):
        return 0  # Custom issue type

    def getSeverity(self):
        return self._severity

    def getConfidence(self):
        return self._confidence

    def getIssueBackground(self):
        return "Issue identified by burpference model analysis"

    def getRemediationBackground(self):
        return "Verify the models findings and remediate accordingly"

    def getIssueDetail(self):
        return self._detail

    def getRemediationDetail(self):
        return None

    def getHttpMessages(self):
        return self._httpMessages

    def getHttpService(self):
        return self._httpService
