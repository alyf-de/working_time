# Copyright (c) 2023, ALYF GmbH and contributors
# For license information, please see license.txt

import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def after_install():
    make_custom_fields()
    insert_docs()


def make_custom_fields():
    create_custom_fields(frappe.get_hooks("working_time_custom_fields"))


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
