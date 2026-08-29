def get_jira_issue_url(jira_site, key):
	return f"https://{jira_site}/browse/{key}" if key and jira_site else None
