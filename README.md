# Support Triage Agent

This is a simple terminal-based agent that processes support tickets and decides whether to reply or escalate.

## What it does

For each ticket, the agent:
- reads the issue, subject, and company
- classifies the type of request
- searches the support documents for relevant information
- decides whether it is safe to respond or should be escalated
- generates a response if a good answer is found
- writes everything to output.csv

The output format follows the required columns:
issue, subject, company, response, product_area, status, request_type, justification

---

## How I approached the problem

I broke the system into three parts: classification, retrieval, and decision.

### Classification
I used simple rule-based logic to identify:
- product issues
- bugs
- invalid or unsafe requests
- sensitive cases like payments, fraud, or account access

### Retrieval
I built a basic retrieval system using:
- sentence-transformers for embeddings
- FAISS for similarity search

Steps:
- cleaned the support documents to remove noise
- split them into chunks
- created embeddings
- searched using the user query
- filtered results by domain (Claude, HackerRank, Visa)

I also retrieve multiple chunks and try the top few instead of relying on just one.

### Decision logic
The system is intentionally conservative.

It escalates when:
- the request is sensitive (payment, fraud, account issues)
- no relevant documentation is found
- the company is missing or unclear
- the retrieval confidence is weak

It replies only when:
- relevant content is found
- a clean and meaningful response can be extracted

### Response generation
Responses are:
- taken directly from retrieved content
- cleaned to remove links, headings, and formatting noise
- kept short and readable

---

## Terminal output

While running, the agent shows:
- a progress bar
- confidence score for each query
- a final summary (total, replied, escalated)

---

## How to run

From the project root:

python code/main.py

This will generate:

support_tickets/output.csv

---

## Notes

- only the provided support data is used
- no external APIs are used
- the system prefers escalation over incorrect answers
- a confidence threshold is used to avoid weak responses

---

## Limitations

- some valid tickets may still be escalated
- response quality depends on the available documents