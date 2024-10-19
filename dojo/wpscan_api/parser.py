import hashlib
import json
from urllib.parse import urlparse
from dojo.models import Endpoint, Finding


class WpscanAPIParser(object):
    """
    Wpscan API
    """

    def get_scan_types(self):
        return ["Wpscan API Scan"]

    def get_label_for_scan_types(self, scan_type):
        return "Wpscan API Scan"

    def get_description_for_scan_types(self, scan_type):
        return "Wpscan API report file can be imported in JSON format (option --json)."

    def get_findings(self, file, test):
        tree = json.load(file)
        dupes = dict()

        for vulns in tree:
            for node in vulns['vulnerabilities']:
                finding = Finding(test=test)
                title = f"{node['customer']}_{node['server_type']}_{node['title']}"
                finding.title = title
            
                finding.description = node['title']
                finding.component_name = node['slug']
                finding.cwe=1395
                finding.vuln_id_from_tool = node['id']
                if node['poc'] == None and node['fixed_in'] != None:
                    finding.severity = 'Medium'
                else: 
                    finding.severity = 'High'

                if node['fixed_in'] != None:
                    pass

                finding.url = node['site_url']
                finding.unsaved_endpoints = list()

                # internal de-duplication
                dupe_key = hashlib.sha256(str(finding.title + finding.url).encode('utf-8')).hexdigest()

                if dupe_key in dupes:
                    find = dupes[dupe_key]
                    if finding.description:
                        find.description += "\n" + finding.description
                    find.unsaved_endpoints.extend(finding.unsaved_endpoints)
                    dupes[dupe_key] = find
                else:
                    dupes[dupe_key] = finding

        return list(dupes.values())

    def convert_severity(self, num_severity):
        """Convert severity value"""
        if num_severity >= -10:
            return "Low"
        elif -11 >= num_severity > -26:
            return "Medium"
        elif num_severity <= -26:
            return "High"
        else:
            return "Info"

