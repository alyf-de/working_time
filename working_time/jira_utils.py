from working_time.jira_client import JiraClient


def get_jira_issue_url(jira_site, key):
	return f"https://{jira_site}/browse/{key}" if key and jira_site else None


def get_description(jira_site, key, note):
	if key and jira_site:
		description = f"{JiraClient(jira_site).get_issue_summary(key)} ({key})"
	elif key:
		description = key
	else:
		description = note or "-"

	if key and note:
		description += f":\n\n{note}"

	return description.strip()
