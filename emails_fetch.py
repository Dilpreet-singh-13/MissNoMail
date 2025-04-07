import os
import datetime
import base64
from typing import List, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from bs4 import BeautifulSoup

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def create_service():
    """
    Returns the discovery service that can be used to access the Gmail APIs. Uses OAuth for credentials.
    """

    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)

        with open("token.json", "w") as token:
            token.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def get_recent_email_subjects(past_days: int = 1) -> List[Tuple[str, str]]:
    """
    Retrieves the subjects of emails sent within the past `past_days` days.

    Args:
        days (int, optional): The number of days to look back for emails. Defaults to 1.

    Returns:
        List[Tuple[str, str]] : List of tuples, where each tuple contains (subject, email_id)
    """

    gmail_service = create_service()

    date_after = (
        datetime.datetime.now() - datetime.timedelta(days=past_days)
    ).strftime("%Y/%m/%d")

    try:
        result = (
            gmail_service.users()
            .messages()
            .list(
                userId="me",
                includeSpamTrash=False,
                q=f"after:{date_after}",
            )
            .execute()
        )
    except HttpError as e:
        print(f"An error occured: {e}")

    message_ids = [message.get("id", "") for message in result.get("messages", [])]

    subjects_and_ids = []
    for id in message_ids:
        try:
            full_message = (
                gmail_service.users()
                .messages()
                .get(userId="me", id=id, format="metadata")
                .execute()
            )
            payload = full_message.get("payload")
        except HttpError as e:
            print(f"An error occured: {e}")

        for header in payload.get("headers", []):
            if header.get("name").lower() == "subject":
                subject = header.get("value")
                break

        # add the tuple of the subject and the corresponding ID to the list
        subjects_and_ids.append((subject, id))

    return subjects_and_ids


def parse_html(data: str) -> str:
    soup = BeautifulSoup(data, "html.parser")
    return soup.get_text(separator="\n").strip()


def extract_payload_data(payload) -> str:
    """
    Extracts the body data from the given payload. Handles multipart emails and base 64 decoding.

    The response structure of the .get() message Gmail API call can be found here:
        https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.messages#Message
    """

    body_text = []

    # if part is text/plain or text/HTML: extract it
    # also serves as the exit condition for recursive calls
    if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get(
        "data", ""
    ):
        body_text.append(
            base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        )
    elif payload.get("mimeType") == "text/html" and payload.get("body", {}).get(
        "data", ""
    ):
        decoded_text = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        body_text.append(parse_html(decoded_text))

    # Handle multiple parts
    if payload.get("parts"):
        # all subparts represent the same data
        if payload.get("mimeType") == "multipart/alternative":
            # we prefer to extract HTML
            for part in payload.get("parts"):
                if part.get("mimeType") == "text/plain":
                    body_text.append(extract_payload_data(part))
        elif payload.get("mimeType").startswith("multipart/"):
            for part in payload.get("parts"):
                body_text.append(extract_payload_data(part))

    return "\n".join(filter(None, body_text)).strip()


def get_email_body(email_id: str) -> str:
    """
    Retrives the body text of a email specified by the email ID.

    Args:
        email_id (str): ID of the email whose body data needs to be extracted.

    Returns:
        str: Extracted data from the body of the email.
    """
    gmail_service = create_service()
    try:
        full_message = (
            gmail_service.users()
            .messages()
            .get(userId="me", id=email_id, format="full")
            .execute()
        )
        payload = full_message.get("payload")
    except HttpError as e:
        print(f"An error occured: {e}")

    email_body = extract_payload_data(payload)
    return email_body
