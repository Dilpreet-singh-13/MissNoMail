import os
import json
from typing import List, Tuple
from pydantic import BaseModel, ValidationError

from dotenv import load_dotenv
from google import genai
from google.genai import types
from googleapiclient.errors import HttpError


def get_llm_client():
    """Returns the gemini client that can be used to access the gemini API."""
    # Uncomment for local running
    # load_dotenv()
    # api_key = os.getenv("GEMINI_API_KEY")

    # For use in Github Actions
    api_key = os.environ.get("GEMINI_API_KEY")

    return genai.Client(api_key=api_key)


def filter_hiring_emails(email_data: List[Tuple[str, str]]) -> List[str]:
    """
    Uses an LLM (API) to find any emails that could be related to internships/ job hiring and discard the rest.
    Uses the email subjects to rule out the emails that are NOT related to internships/ job hiring and return the rest.

    Args:
        email_data (List[Tuple[str, str]]): List of tuples having (email-subject, corresponding-email-id)

    Returns:
        List[str]: List of `email-id` corresponding to the filtered emails.
    """

    SYSTEM_PROMPT = """
    You are given a list of email subjects and its corresponding ID.
    So you have this data:
        1. The email subject
        2. The corresponding email id
    
    You task is to filter out any emails that does not seem to be related to internships or job hiring from reading the contents of the email subject and then return a list containing the email ids of the emails that are left, i.e that are realted to internships or job hiring.
    
    There will be many emails with subjects related to topics like: lost and found, Hackathons, emails from university clubs/societies, workshops, seminars etc, you need to rule out such emails and DON'T include them in the reply.
    
    If you are unsure where the email is realted to internships or job hiring on the basis of the subject along, include that email ID in the reply regardless.
    
    Input example:
        [('Invitation to Workshop on Product Design and Development by Prof. XYZ', '195d64s7h1eb0ac3'), ('Fwd: UPDATE: JPMorganChase | Online Test Instructions - Summer Internship 2026', '195h4dhefd18dbf2'), ('Fwd: Lost Book Found', '195d5b048cc11157'), ('@ UG 6th Sem and above /PG : Summer internship at NIT, Warangal, Telangana', '1912186480d8d4av')]
    
    Return example based on the above reply (return email IDs seperated by a space): 
        195h4dhefd18dbf2 1912186480d8d4av
    """

    llm_client = get_llm_client()

    # Uncomment for local running
    # load_dotenv()
    # model = os.getenv("LLM_MODEL")

    # For use in Github Actions
    model = os.environ.get("LLM_MODEL")

    try:
        response = llm_client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            contents=email_data,
        )
    except HttpError as e:
        print(f"An error occured: {e}")

    email_ids = [id for id in response.text.split(" ")]
    return email_ids


class ResponseSchema(BaseModel):
    company_name: str
    position: str
    application_link: str
    application_deadline: str
    requirements: list[str]
    other: list[str]


def extract_email_details(email_body: str) -> ResponseSchema | None:
    """Extracts important details from the body of 'hiring' realted emails and returns a structured response.
    Extracts details like (if applicable):
        - Company name
        - Position hiring for (intern, SDE etc)
        - Application link
        - Application deadline
        - Requirements

    Args:
        email_body (str): data in the body of the email

    Returns:
        Dict[str, str]: JSON like dictionary containing the extracted details
    """

    SYSTEM_PROMPT = """
    You are given the extracted text from emails realted to internships/job hiring. You task is to extract important imformation from the text and give a structured response in the form of an JSON object.
    
    Extracts details like (if applicable):
        - Company name
        - Position hiring for (intern, SDE etc)
        - Application link
        - Application deadline
        - Requirements (List)
        - Other (List)

    - If any of the above details are not mentioned/found in the text simlpy set the value of that field to "Not Found".
    - Requirements and Other are lists, you can fill them will "Not Found" as per the above instruction.
    - The "Other" fields can have any other information that seems important from the email text.
    - The email text may have a lot of unnecessary information like "why join us", anything after "Thanks, regards" etc, no need to use and give such info.
    - Check for false positives, some text given to you may not be related to internships/job hiring. In such case just put the value "False Positive" in all the fields.
    
    Return example:
    {
        "company_name": "ABC",
        "position": "ML intern",
        "application_link": "xyz.com",
        "application_deadline": "28/3/2025 9pm",
        "requirements": [
            "CGPA > 8",
            "Python"
        ],
        "other": [
            "Stipend = $100"
        ]
    }
    """
    llm_client = get_llm_client()
    # Uncomment for local running
    # load_dotenv()
    # model = os.getenv("LLM_MODEL")

    # For use in Github Actions
    model = os.environ.get("LLM_MODEL")

    try:
        response = llm_client.models.generate_content(
            model=model,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type="application/json",
                response_schema=ResponseSchema,
            ),
            contents=email_body,
        )
    except HttpError as e:
        print(f"An error occured: {e}")
        return None

    try:
        response_dict = json.loads(response.text)
        return ResponseSchema.model_validate(response_dict)
    except (ValidationError, json.JSONDecodeError) as e:
        print(f"Parse error: {e}")
        return None
