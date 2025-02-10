import os
import json
from datetime import datetime
from consts import PROJECT_ROOT, LOG_DIR


class BurpDBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = os.path.join(LOG_DIR, "findings.json")
        self.db_path = db_path
        print("[*] DB Path: %s" % self.db_path)
        self._ensure_db_dir()
        self._findings = self._load_findings()
        print("[*] Loaded %d findings" % len(self._findings))

    def _ensure_db_dir(self):
        """Ensure the database directory exists"""
        db_dir = os.path.dirname(self.db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir)

    def _load_findings(self):
        """Load findings from JSON file"""
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print("[!] Error loading findings: %s" % str(e))
                return []
        return []

    def _save_findings(self):
        """Save findings to JSON file"""
        try:
            with open(self.db_path, "w") as f:
                json.dump(self._findings, f, indent=2)
            print("[+] Saved %d findings to %s" % (len(self._findings), self.db_path))
        except Exception as e:
            print("[!] Error saving findings: %s" % str(e))

    def add_finding(self, finding):
        """Add a new finding"""
        finding["timestamp"] = datetime.now().isoformat()
        self._findings.append(finding)
        self._save_findings()

    def get_findings(self, filters=None):
        """Retrieve findings with optional filters"""
        if not filters:
            return self._findings

        filtered = []
        for finding in self._findings:
            matches = True
            for key, value in filters.items():
                if key not in finding or finding[key] != value:
                    matches = False
                    break
            if matches:
                filtered.append(finding)

        return filtered
