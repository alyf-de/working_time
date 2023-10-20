from working_time.jira_client import JiraClient


def get_jira_issue_url(jira_site, key):
    return f"https://{jira_site}/browse/{key}" if key else None


def get_description(jira_site, key, note):
    invoice_note = (
        note.strip().lstrip("+").strip()
        if note and note.strip().startswith("+")
        else None
    )
    if key:
        description = f"{JiraClient(jira_site).get_issue_summary(key)} ({key})"
        if invoice_note:
            description += f":\n\n{invoice_note}"
        return description.strip()
    elif invoice_note:
        return invoice_note
    else:
        return "-"
