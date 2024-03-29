from . import __version__ as app_version

app_name = "working_time"
app_title = "Working Time"
app_publisher = "ALYF GmbH"
app_description = "-"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "hallo@alyf.de"
app_license = "-"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/working_time/css/working_time.css"
# app_include_js = "/assets/working_time/js/working_time.js"

# include js, css files in header of web template
# web_include_css = "/assets/working_time/css/working_time.css"
# web_include_js = "/assets/working_time/js/working_time.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "working_time/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "working_time.install.before_install"
after_install = "working_time.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "working_time.uninstall.before_uninstall"
# after_uninstall = "working_time.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "working_time.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
#	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
#	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
#	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
#	"*": {
#		"on_update": "method",
#		"on_cancel": "method",
#		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
#	"all": [
#		"working_time.tasks.all"
#	],
#	"daily": [
#		"working_time.tasks.daily"
#	],
#	"hourly": [
#		"working_time.tasks.hourly"
#	],
#	"weekly": [
#		"working_time.tasks.weekly"
#	]
#	"monthly": [
#		"working_time.tasks.monthly"
#	]
# }

# Testing
# -------

# before_tests = "working_time.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
#	"frappe.desk.doctype.event.event.get_events": "working_time.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
#	"Task": "working_time.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
#	"working_time.auth.validate"
# ]

working_time_custom_fields = {
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
	],
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
			"fieldname": "jira_site",
			"label": "Site",
			"fieldtype": "Link",
			"options": "Jira Site",
			"insert_after": "jira_section",
			"translatable": 0,
		},
	],
	"Timesheet": [
		{
			"fieldname": "working_time",
			"label": "Working Time",
			"fieldtype": "Link",
			"options": "Working Time",
			"insert_after": "project",
			"translatable": 0,
			"read_only": 1,
		},
		{
			"fieldname": "freelancer_time",
			"label": "Freelancer Time",
			"fieldtype": "Link",
			"options": "Freelancer Time",
			"insert_after": "working_time",
			"translatable": 0,
			"read_only": 1,
		},
	],
	"Attendance": [
		{
			"fieldname": "working_time",
			"label": "Working Time",
			"fieldtype": "Link",
			"options": "Working Time",
			"insert_after": "company",
			"translatable": 0,
			"read_only": 1,
		}
	],
}
