# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt


import json

import frappe
from frappe import _
import requests
from requests.auth import HTTPBasicAuth


class JiraClient:
    def __init__(self, jira_site: str) -> None:
        jira_site = frappe.get_doc("Jira Site", jira_site)

        self.url = f"https://{jira_site.name}"
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(
            jira_site.username, jira_site.get_password(fieldname="api_token")
        )
        self.session.headers = {"Accept": "application/json"}

    def get(self, url: str, params=None):
        response = self.session.get(url, params=params)

        try:
            response.raise_for_status()
        except requests.HTTPError:
            error_text = json.loads(response.text)
            error_message = (
                error_text.get("errorMessage")
                or (error_text.get("errorMessages") or [None])[0]
                or "Something went wrong."
            )

            frappe.throw(f"{url}: {_(error_message)}")

        return response.json()

    def get_issue_summary(self, key: str) -> str:
        url = f"{self.url}/rest/api/2/issue/{key}"
        params = {
            "fields": "summary",
        }

        return self.get(url, params=params).get("fields").get("summary")
