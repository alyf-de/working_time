# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    customize_project()
    customize_timesheet()
    insert_docs()


def customize_project():
    custom_fields = {
        "Project": [
            {
                "fieldname": "billing_rate",
                "label": "Billing Rate per Hour",
                "fieldtype": "Currency",
                "options": "currency",
                "insert_after": "cost_center",
                "translatable": 0,
            },
            {
                "fieldname": "jira_section",
                "label": "Jira",
                "fieldtype": "Section Break",
                "insert_after": "message",
                "collapsible": 1,
            },
            {
                "fieldname": "jira_site_url",
                "label": "Site URL",
                "fieldtype": "Data",
                "insert_after": "jira_section",
                "description": "e.g. mysite.atlassian.net",
                "translatable": 0,
            },
        ]
    }

    create_custom_fields(custom_fields)


def customize_timesheet():
    custom_fields = {
        "Timesheet Detail": [
            {
                "fieldname": "jira_section",
                "label": "Jira",
                "fieldtype": "Section Break",
                "insert_after": "costing_amount",
            },
            {
                "fieldname": "jira_issue_url",
                "label": "Issue URL",
                "fieldtype": "Data",
                "Options": "URL",
                "insert_after": "jira_section",
                "read_only": 1,
                "translatable": 0,
            },
        ]
    }

    create_custom_fields(custom_fields)


def insert_docs():
    docs = [
        {
            "doctype": "Activity Type",
            "activity_type": "Default",
        }
    ]

    for doc in docs:
        filters = doc.copy()

        # Clean up filters. They need to be a plain dict without nested dicts or lists.
        for key, value in doc.items():
            if isinstance(value, (list, dict)):
                del filters[key]

        if not frappe.db.exists(filters):
            frappe.get_doc(doc).insert(ignore_if_duplicate=True)
