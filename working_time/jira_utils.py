from working_time.jira_client import JiraClient


def get_jira_issue_url(jira_site, key):
    return f"https://{jira_site}/browse/{key}" if key else None


def get_description(jira_site, key, note):
    if key:
        description = f"{JiraClient(jira_site).get_issue_summary(key)} ({key})"
        if note:
            description += f":\n\n{note}"
        return description.strip()
    elif note:
        return note
    else:
        return "-"
