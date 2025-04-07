import os
import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
from pathlib import Path

import markdown
from dotenv import load_dotenv
from jinja2 import Template
from emails_fetch import get_recent_email_subjects, get_email_body
from llm_utils import filter_hiring_emails, extract_email_details

from llm_utils import ResponseSchema

DAYS = 1

template_str = """
# Intern/Job realted email after {{date}}

{% for job in jobs %}
## {{loop.index}}. {{job.company_name}}

**Postion:** {{job.position}}

**Link:** {{job.application_link}}

**Deadline:** {{job.application_deadline}}

**Requirements:**
{% for req in job.requirements %}
- {{req}}
{% endfor %}

**Other:**
{% if job.other %}
{% for info in job.other %}
- {{ info }}
{% endfor %}
{% else %}
None
{% endif %}

---

{% endfor %}
"""


def send_email(
    jobs_list: List[ResponseSchema], template_content: str, subject: str = ""
) -> None:
    """Sends the email using the HTML template.
    Takes the Sender's email, password and the recipient's email from the env variables (.env file).
    Also handles sending a simple notification email, for this the job_list = [] and template_content = "", ie both should be empty.

    Args:
        jobs_list (List[ResponseSchema]): list of object containing all the info to be sent.
        template_content (str): the template which can be filled with the data and sent. Is converted to jinja2 Template object.
        subject (str, optional): Subject of the email.
    """
    env_path = Path(".env")
    if env_path.exists():
        # for local running
        load_dotenv()
        sender_email = os.getenv("SENDER_GMAIL_ADDRESS", "")
        receiver_email = os.getenv("RECEIVER_GMAIL_ADDRESS", "")
        APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")
    else:
        # For use in Github Actions
        sender_email = os.environ.get("SENDER_GMAIL_ADDRESS", "")
        receiver_email = os.environ.get("RECEIVER_GMAIL_ADDRESS", "")
        APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    date_after = (datetime.datetime.now() - datetime.timedelta(days=DAYS)).strftime(
        "%Y/%m/%d"
    )

    if not jobs_list and not template_content:
        email_text = "No relevant emails found."
    else:
        template = Template(template_content)
        email_text = template.render(date=date_after, jobs=jobs_list)

    html_body = markdown.markdown(
        email_text, extensions=["extra"]
    )  # extension for richer markdwon support

    msg.attach(MIMEText(email_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)  # connect to Gmail's SMPT server
        server.starttls()  # secure connection
        server.login(sender_email, APP_PASSWORD)

        server.send_message(msg)
        print("Email Sent Sucessfully!")
    except Exception as e:
        print(f"An error occured while sending the email: {e}")
    finally:
        server.quit()


def main():
    SUBJECT = "Daily python script response"

    email_subjects_ids = get_recent_email_subjects(DAYS)
    if not email_subjects_ids:
        send_email([], "", SUBJECT)
        return

    filtered_email_ids = filter_hiring_emails(email_subjects_ids)
    if not filtered_email_ids:
        send_email([], "", SUBJECT)
        return

    job_details_list = []
    for i, email_id in enumerate(filtered_email_ids):
        email_body = get_email_body(email_id.strip())
        if not email_body:
            continue
        details = extract_email_details(email_body)
        if details:
            job_details_list.append(details)

    send_email(job_details_list, template_str, SUBJECT)


if __name__ == "__main__":
    main()
