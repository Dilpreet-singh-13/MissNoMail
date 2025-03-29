# MissNoMail

MissNoMail is an automated email filtering tool that extracts job and internship opportunities from your Gmail inbox and delivers them in a neatly organized digest.

## 🎯 Motivation and Overview

**Are you someone who gets a lot of emails and spends time looking for the right ones?**

I do face this problem, beneath all the emails I receive daily there are emails related to internships/job opportunities and it's really easy to miss those. Most of them have an application deadline which can be easily missed if you don't check the email on time.

MissNoMail solves this problem of missing important career opportunities buried in your inbox. Using the Gmail API and Google's Gemini AI.

### 🔍 How does it work?

1. Scans your recent emails using the Gmail API. (default: past 1 day)
2. Intelligently filters and removes irrelevant emails based on email subject using a LLM.
3. Retrieves the full body contents of the remaining relevant emails.
4. Extracts structured information from each opportunity:
    - Company name
    - Position details
    - Application link
    - Deadline
    - Requirements
    - Other important info
5. Compiles everything into a clean, organized digest, a markdown-based email (plain text & HTML)
6. Delivers the digest directly to your inbox.

### ✨ Features

- **Smart Filtering:** Uses AI to identify job-related emails with high accuracy.
- **Structured Format:** Presents opportunities in a consistent, easy-to-read format.
- **Daily Automation:** Set it and forget it - receive digests automatically.
- **Customizable:** Adjust the time window, search criteria, and more.

### ⚡ Customization

- To change the search time window, change the `DAYS` constant in `main.py`
- To change the digest template, change the `template_str` in `main.py`
- Filtering and data extraction can be customized by modifying the `SYSTEM_PROMPT` in `llm_utils.py`
- Any LLM model/API can be used

## 💻 Run Locally

**Prerequisites:**
- Python 3.10.7 or greater installed
- A Google account with Gmail enabled.

1. Clone the project and install dependencies

    ```bash
    # Clone the repository
    git clone https://github.com/Dilpreet-singh-13/MissNoMail.git
    cd MissNoMail

    # Set Up a Virtual Environment
    python -m venv venv
    venv\Scripts\activate  # On Unix or MacOS use `source venv/bin/activate`

    # Install dependencies
    pip install -r requirements.txt
    ```

2. Setup Google Cloud project

    - Enable the Gmail API from the Google Cloud console
    - Configure the OAuth Consent Screen
    - Details of these steps are mentioned on the [Gmail API quickstart page](https://developers.google.com/workspace/gmail/api/quickstart/python).

    > [!IMPORTANT]  
    > As this script requires a **restricted** scope, the script needs to be submitted for verification if you want it to be usable by everyone. But for personal use, you can simply add yourself as a test user under the Audience page in the Google Cloud console and use the script.

3. Setup environment variables

    ```bash
    cp .env.example .env
    # Edit .env with your API keys and email settings
    ```

4. To run the script manually

    On first run, the app will open a browser window for authentication.

    ```bash
    python main.py
    ```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ✅ To-Do

- [ ] Automate and schedule the script using Github Actions