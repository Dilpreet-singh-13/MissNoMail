import os
import smtplib
from datetime import date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List

import markdown
from dotenv import load_dotenv
from jinja2 import Template
from emails_fetch import get_recent_email_subjects, get_email_body
from llm_utils import filter_hiring_emails, extract_email_details

from llm_utils import ResponseSchema

DAYS = 1

template_str = """
# All intern/job realted email for {{today}}

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

    Args:
        jobs_list (List[ResponseSchema]): list of object containing all the info to be sent.
        template (str): the template which can be filled with the data and sent. Is converted to jinja2 Template object.
        subject (str, optional): Subject of the email.
    """

    load_dotenv()
    sender_email = os.getenv("SENDER_GMAIL_ADDRESS", "")
    receiver_email = os.getenv("RECEIVER_GMAIL_ADDRESS", "")

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    template = Template(template_content)
    email_text = template.render(today=date.today(), jobs=jobs_list)

    html_body = markdown.markdown(
        email_text, extensions=["extra"]
    )  # extension to get richer markdwon support

    msg.attach(MIMEText(email_text, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)  # connect to Gmail's SMPT server
        server.starttls()  # secure connection
        server.login(sender_email, os.getenv("GMAIL_APP_PASSWORD", ""))

        server.send_message(msg)
        print("Email Sent Sucessfully!")
    except Exception as e:
        print(f"An error occured while sending the email: {e}")
    finally:
        server.quit()


def main():
    email_subjects_ids = get_recent_email_subjects(DAYS)
    filtered_email_ids = filter_hiring_emails(email_subjects_ids)

    job_details_list = []
    for i, email_id in enumerate(filtered_email_ids):
        email_body = get_email_body(email_id.strip())
        details = extract_email_details(email_body)
        job_details_list.append(details)

    SUBJECT = "Daily python script response"
    send_email(job_details_list, template_str, SUBJECT)


if __name__ == "__main__":
    main()
