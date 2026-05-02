import pandas as pd
import re
from tqdm import tqdm

from agent.classifier import classify_ticket
from retrieval.retriever import load_data, build_index, search


def safe_text(val):
    if pd.isna(val):
        return ""
    return str(val)


# improved response builder (tries top 3 docs)
def build_response(docs):
    if not docs:
        return ""

    for d in docs[:3]:
        text = d["text"]

        # clean noise
        text = re.sub(r'http\S+', '', text)
        text = re.sub(r'\[.*?\]', '', text)
        text = re.sub(r'\(.*?\)', '', text)
        text = re.sub(r'#+\s*', '', text)
        text = re.sub(r'screen\/\S+', '', text)
        text = re.sub(r'md\)', '', text)

        text = text.replace("-", " ")
        text = text.replace("%3F", "")

        sentences = text.split(".")

        for s in sentences:
            clean = s.strip()

            if (
                60 < len(clean) < 180 and
                clean and clean[0].isupper() and
                clean.endswith((".", "!", "?")) and
                "http" not in clean and
                "[" not in clean and
                "]" not in clean and
                "/" not in clean
            ):
                return "According to our support documentation, " + clean

    return ""


# load once
load_data()
build_index()

input_file = "support_tickets/support_tickets.csv"
output_file = "support_tickets/output.csv"

df = pd.read_csv(input_file)

rows = []

for _, row in tqdm(df.iterrows(), total=len(df), desc="Processing tickets"):
    issue = safe_text(row.get("Issue"))
    subject = safe_text(row.get("Subject"))
    company = safe_text(row.get("Company")).strip()

    query = issue + " " + subject
    query_lower = query.lower()

    result = classify_ticket(issue, subject, company)

    domain = result.get("domain")
    request_type = result.get("request_type", "invalid")
    product_area = result.get("product_area", "unknown")

    if domain not in ["claude", "hackerrank", "visa"]:
        domain = None

    # improved retrieval
    docs = search(query, k=5, domain=domain)

    confidence = None
    if docs:
        confidence = docs[0]["score"]
        print(f"[INFO] Confidence: {round(confidence, 2)}")

    # conversational handling
    if any(x in query_lower for x in ["thank you", "thanks", "appreciate", "great help"]):
        rows.append({
            "issue": issue,
            "subject": subject,
            "company": company,
            "response": "You're welcome. Let us know if you need further help.",
            "product_area": product_area,
            "status": "replied",
            "request_type": request_type,
            "justification": "Non-support conversational message"
        })
        continue

    escalate = False

    # safety rules
    if result.get("is_malicious"):
        escalate = True

    if result.get("urgency") == "high":
        escalate = True

    if not docs:
        escalate = True

    if domain is None or company.lower() == "none":
        escalate = True

    if any(w in query_lower for w in [
        "refund", "charge", "billing", "payment",
        "account", "access", "password", "login",
        "fraud", "stolen", "unauthorized"
    ]):
        escalate = True

    if len(query_lower.strip()) < 10:
        escalate = True

    # confidence threshold
    if confidence is not None and confidence > 1.2:
        escalate = True

    if escalate:
        status = "escalated"
        response = "This issue requires further review by our support team."

        # improved justification
        if result.get("is_malicious"):
            justification = "Escalated due to malicious or unsafe request"
        elif result.get("urgency") == "high":
            justification = "Escalated due to high-risk or sensitive issue"
        elif not docs:
            justification = "Escalated due to no supporting documentation"
        elif confidence is not None and confidence > 1.2:
            justification = "Escalated due to low retrieval confidence"
        else:
            justification = "Escalated due to unclear request"

    else:
        response = build_response(docs)

        if not response or len(response) < 40:
            status = "escalated"
            response = "This issue requires further review by our support team."
            justification = "Escalated due to insufficient documentation"
        else:
            status = "replied"
            if confidence is not None:
                justification = f"Response based on retrieved support documentation (score={round(confidence, 2)})"
            else:
                justification = "Response based on retrieved support documentation"

    rows.append({
        "issue": issue,
        "subject": subject,
        "company": company,
        "response": response,
        "product_area": product_area,
        "status": status,
        "request_type": request_type,
        "justification": justification
    })


out = pd.DataFrame(rows)

out = out[
    ["issue", "subject", "company", "response",
     "product_area", "status", "request_type", "justification"]
]

out.to_csv(output_file, index=False)

print("\nDone — final output generated")

# summary
total = len(out)
replied = len(out[out["status"] == "replied"])
escalated = len(out[out["status"] == "escalated"])

print("\nSummary:")
print(f"Total tickets: {total}")
print(f"Replied: {replied}")
print(f"Escalated: {escalated}")