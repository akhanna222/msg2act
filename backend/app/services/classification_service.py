"""
LLM-based email classification service
Auto-tags emails with user-defined categories
"""
from typing import List, Dict, Optional
import json
from openai import OpenAI

from app.core.config import settings
from app.models.email_category import EmailCategory
from app.models.message import Message


class EmailClassificationService:
    """
    Classifies emails into user-defined categories using LLM
    """

    def __init__(self):
        if settings.OPENAI_API_KEY:
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        else:
            self.client = None

    def classify_email(
        self,
        message: Message,
        categories: List[EmailCategory],
        generate_urgency: bool = True,
    ) -> List[Dict]:
        """
        Classify an email into categories

        Args:
            message: Message to classify
            categories: List of available categories
            generate_urgency: Whether to detect urgency

        Returns:
            List of classifications with confidence scores
            [
                {
                    "category_id": "uuid",
                    "category_name": "Invoice",
                    "confidence": 0.95,
                    "is_urgent": False,
                    "urgency_reason": None,
                    "extracted_data": {"invoice_number": "INV-123", ...}
                }
            ]
        """
        if not self.client:
            return []  # No OpenAI key, skip classification

        # Build category descriptions for LLM
        category_descriptions = []
        for cat in categories:
            desc = {
                "id": str(cat.id),
                "name": cat.name,
                "description": cat.description or "",
            }
            if cat.example_subjects:
                desc["examples"] = cat.example_subjects
            category_descriptions.append(desc)

        # Prepare email content
        email_content = f"""
Subject: {message.subject or '(No subject)'}
From: {message.from_email}
Date: {message.received_at}

Body:
{(message.body_text or '')[:2000]}  # Limit to 2000 chars
"""

        # Build prompt
        prompt = f"""You are an email classification assistant. Analyze the following email and classify it into the most relevant categories.

Available Categories:
{json.dumps(category_descriptions, indent=2)}

Email to Classify:
{email_content}

Tasks:
1. Identify which categories apply (can be multiple)
2. For each category, provide a confidence score (0-1)
3. Extract relevant structured data for each category
4. Determine if the email is urgent and why

Return JSON format:
{{
  "classifications": [
    {{
      "category_id": "uuid",
      "category_name": "Invoice",
      "confidence": 0.95,
      "is_urgent": false,
      "urgency_reason": null,
      "extracted_data": {{"invoice_number": "INV-123", "amount": 1500, "due_date": "2024-12-31"}}
    }}
  ]
}}

Only include categories with confidence > 0.5.
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert email classifier. Always return valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            result = json.loads(response.choices[0].message.content)
            return result.get("classifications", [])

        except Exception as e:
            print(f"Classification error: {e}")
            return []

    def generate_default_tags(self, message: Message) -> Dict:
        """
        Generate default tags for common email types
        (Invoice, Receipt, Shipping, Meeting, etc.)

        Args:
            message: Message to tag

        Returns:
            Dict with suggested tags
        """
        if not self.client:
            return {"tags": []}

        email_content = f"""
Subject: {message.subject or '(No subject)'}
From: {message.from_email}

Body:
{(message.body_text or '')[:1500]}
"""

        prompt = f"""Analyze this email and suggest appropriate tags from common categories:
- Invoice
- Receipt
- Flight Booking
- Hotel Booking
- Shipping/Delivery
- Meeting Invite
- Newsletter
- Promotion/Marketing
- Insurance
- Bank Statement
- Urgent
- Action Required
- Informational

Email:
{email_content}

Return JSON:
{{
  "tags": ["Invoice", "Urgent"],
  "urgency_level": "high",  // low, medium, high
  "action_required": true,
  "summary": "Invoice payment due in 3 days"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an email tagging assistant. Return valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"Tagging error: {e}")
            return {"tags": []}

    def extract_structured_data(
        self, message: Message, category: EmailCategory
    ) -> Optional[Dict]:
        """
        Extract structured data for a specific category

        Args:
            message: Message to extract from
            category: Category to extract data for

        Returns:
            Extracted data dict or None
        """
        if not self.client:
            return None

        # Category-specific extraction instructions
        extraction_guides = {
            "Invoice": "Extract: invoice_number, amount, currency, due_date, vendor_name",
            "Flight": "Extract: flight_number, airline, departure_date, departure_airport, arrival_airport, booking_reference",
            "Insurance": "Extract: policy_number, renewal_date, premium_amount, coverage_type",
            "Shipping": "Extract: tracking_number, carrier, expected_delivery, order_number",
            "Meeting": "Extract: meeting_date, meeting_time, meeting_link, attendees, agenda",
        }

        guide = extraction_guides.get(category.name, "Extract relevant information")

        email_content = f"""
Subject: {message.subject or '(No subject)'}
Body: {(message.body_text or '')[:2000]}
"""

        prompt = f"""Extract structured data from this email for category: {category.name}

{guide}

Email:
{email_content}

Return JSON with extracted fields. Use null for missing fields.
"""

        try:
            response = self.client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data extraction assistant. Return valid JSON with extracted fields.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            print(f"Extraction error: {e}")
            return None
