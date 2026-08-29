from working_time.jira_client import JiraClient


def get_jira_issue_url(jira_site, key):
	return f"https://{jira_site}/browse/{key}" if key and jira_site else None


def get_jira_issue_summary(jira_site: str, key: str) -> str:
	issue_summary = JiraClient(jira_site).get_issue_summary(key)
	return f"{issue_summary} ({key})"
