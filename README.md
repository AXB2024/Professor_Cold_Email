# Professor Cold Email Backend

Production-style FastAPI backend that:
- accepts student and professor inputs
- scrapes professor research pages when needed
- summarizes research with an LLM
- generates personalized cold emails with an LLM
- scores/validates personalization quality
- enforces human review before sending
- sends approved emails via Gmail SMTP or Gmail API

## Project Structure

```text
app/
  core/
    config.py
    logging.py
  llm/
    client.py
    prompts.py
  models/
    schemas.py
  routes/
    email_routes.py
  scraper/
    research_scraper.py
  services/
    email_pipeline.py
    gmail_service.py
    personalization_validator.py
    review_store.py
  main.py
requirements.txt
.env.example
```

## Setup

```bash
cd professor-cold-email-backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Fill in `.env` credentials:
- `OPENAI_API_KEY`
- Gmail SMTP or Gmail API values

## Run

```bash
uvicorn app.main:app --reload
```

## API Endpoints

### 1) Generate emails
`POST /generate_emails`

Request body:

```json
{
  "student": {
    "name": "Alex Kim",
    "major": "Computer Science",
    "university": "University of X",
    "skills": ["Python", "PyTorch", "Data analysis"],
    "interests": ["Machine learning", "Computer vision"]
  },
  "professors": [
    {
      "name": "Dr. Jane Doe",
      "email": "jdoe@university.edu",
      "website_url": "https://example.edu/lab"
    },
    {
      "name": "Dr. Ravi Patel",
      "email": "rpatel@university.edu",
      "research_text": "My group studies robust robot planning under uncertainty..."
    }
  ]
}
```

Response includes per-professor:
- `summary`
- `email`
- `score` (0-10)
- `draft_id` for review/send

### 2) Review email
`POST /review_email`

Approve:

```json
{
  "draft_id": "uuid-here",
  "action": "approve"
}
```

Edit:

```json
{
  "draft_id": "uuid-here",
  "action": "edit",
  "edited_email": "updated email body..."
}
```

Reject:

```json
{
  "draft_id": "uuid-here",
  "action": "reject"
}
```

### 3) Send approved email
`POST /send_email`

```json
{
  "draft_id": "uuid-here",
  "provider": "smtp"
}
```

`provider` may be `smtp` or `gmail_api`. If omitted, defaults to `EMAIL_PROVIDER`.

## Notes
- Emails with score `< 7` trigger one auto-regeneration attempt.
- Sending is blocked until draft status is `approved`.
- Sent email logs are written to `logs/sent_emails.log`.

