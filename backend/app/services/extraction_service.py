"""
Entity extraction service using spaCy and regex patterns
"""
import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import spacy
from email.utils import parseaddr

# Load spaCy model (small English model)
# Run: python -m spacy download en_core_web_sm
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    nlp = None


class EntityExtractor:
    """Extract entities from text using NLP and pattern matching"""

    # Currency patterns
    CURRENCY_PATTERNS = [
        r'\$\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # $1,234.56
        r'USD\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # USD 1234.56
        r'€\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # €1,234.56
        r'EUR\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # EUR 1234.56
        r'£\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # £1,234.56
        r'GBP\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # GBP 1234.56
        r'₹\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # ₹1,234.56
        r'INR\s*\d+(?:,\d{3})*(?:\.\d{2})?',  # INR 1234.56
    ]

    # Email pattern
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Phone pattern (basic)
    PHONE_PATTERN = r'[\+]?[(]?[0-9]{1,4}[)]?[-\s\.]?[(]?[0-9]{1,4}[)]?[-\s\.]?[0-9]{1,9}'

    def __init__(self):
        self.nlp = nlp

    def extract_all(self, text: str, from_email: Optional[str] = None) -> Dict[str, List[Dict]]:
        """
        Extract all entity types from text

        Args:
            text: Text to analyze
            from_email: Sender email (for extracting sender info)

        Returns:
            Dictionary with entity types as keys and lists of entities as values
        """
        if not text:
            return {"people": [], "companies": [], "amounts": [], "dates": []}

        entities = {
            "people": self.extract_people(text, from_email),
            "companies": self.extract_companies(text),
            "amounts": self.extract_amounts(text),
            "dates": self.extract_dates(text),
        }

        return entities

    def extract_people(self, text: str, from_email: Optional[str] = None) -> List[Dict]:
        """
        Extract person entities from text

        Args:
            text: Text to analyze
            from_email: Sender email address

        Returns:
            List of person entities with attributes
        """
        people = []

        if not self.nlp:
            return people

        # Use spaCy NER
        doc = self.nlp(text[:100000])  # Limit text length for performance

        for ent in doc.ents:
            if ent.label_ == "PERSON":
                # Get context (surrounding text)
                start = max(0, ent.start_char - 50)
                end = min(len(text), ent.end_char + 50)
                context = text[start:end]

                person = {
                    "name": ent.text,
                    "normalized_name": ent.text.lower().strip(),
                    "context": context,
                    "confidence": 0.8,  # spaCy confidence
                    "attributes": {},
                }

                people.append(person)

        # Extract from email signature (if present)
        signature_people = self._extract_from_signature(text)
        people.extend(signature_people)

        # Extract from email addresses in text
        email_people = self._extract_from_emails(text)
        people.extend(email_people)

        # Add sender if available
        if from_email:
            sender_name, sender_email = parseaddr(from_email)
            if sender_name and sender_name != sender_email:
                people.append({
                    "name": sender_name,
                    "normalized_name": sender_name.lower().strip(),
                    "context": f"Email sender: {from_email}",
                    "confidence": 1.0,
                    "attributes": {"email": sender_email},
                })

        # Deduplicate
        people = self._deduplicate_entities(people)

        return people

    def extract_companies(self, text: str) -> List[Dict]:
        """
        Extract company/organization entities

        Args:
            text: Text to analyze

        Returns:
            List of company entities
        """
        companies = []

        if not self.nlp:
            return companies

        doc = self.nlp(text[:100000])

        for ent in doc.ents:
            if ent.label_ == "ORG":
                start = max(0, ent.start_char - 50)
                end = min(len(text), ent.end_char + 50)
                context = text[start:end]

                company = {
                    "name": ent.text,
                    "normalized_name": ent.text.lower().strip(),
                    "context": context,
                    "confidence": 0.75,
                    "attributes": {},
                }

                companies.append(company)

        # Extract from email domains
        domain_companies = self._extract_from_domains(text)
        companies.extend(domain_companies)

        # Deduplicate
        companies = self._deduplicate_entities(companies)

        return companies

    def extract_amounts(self, text: str) -> List[Dict]:
        """
        Extract monetary amounts

        Args:
            text: Text to analyze

        Returns:
            List of amount entities
        """
        amounts = []

        for pattern in self.CURRENCY_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)

            for match in matches:
                amount_str = match.group()

                # Parse currency and value
                currency, value = self._parse_currency(amount_str)

                # Get context
                start = max(0, match.start() - 100)
                end = min(len(text), match.end() + 100)
                context = text[start:end]

                amounts.append({
                    "name": amount_str,
                    "normalized_name": f"{currency}_{value}",
                    "context": context,
                    "confidence": 0.9,
                    "attributes": {
                        "value": value,
                        "currency": currency,
                        "raw": amount_str,
                    },
                })

        return amounts

    def extract_dates(self, text: str) -> List[Dict]:
        """
        Extract date entities

        Args:
            text: Text to analyze

        Returns:
            List of date entities
        """
        dates = []

        if not self.nlp:
            return dates

        doc = self.nlp(text[:100000])

        for ent in doc.ents:
            if ent.label_ == "DATE":
                start = max(0, ent.start_char - 50)
                end = min(len(text), ent.end_char + 50)
                context = text[start:end]

                dates.append({
                    "name": ent.text,
                    "normalized_name": ent.text.lower().strip(),
                    "context": context,
                    "confidence": 0.7,
                    "attributes": {
                        "raw_text": ent.text,
                    },
                })

        return dates

    def _extract_from_signature(self, text: str) -> List[Dict]:
        """Extract people from email signatures"""
        people = []

        # Common signature patterns
        signature_markers = [
            "best regards",
            "regards",
            "sincerely",
            "thanks",
            "thank you",
            "cheers",
        ]

        text_lower = text.lower()

        for marker in signature_markers:
            if marker in text_lower:
                # Get text after the marker (likely signature)
                idx = text_lower.rfind(marker)
                signature = text[idx : idx + 500]

                # Look for names (lines with capital letters, not too long)
                lines = signature.split("\n")
                for line in lines[:5]:  # Check first 5 lines
                    line = line.strip()
                    if (
                        2 < len(line) < 50
                        and any(c.isupper() for c in line)
                        and not line.startswith("http")
                        and "@" not in line
                    ):
                        # Likely a name
                        people.append({
                            "name": line,
                            "normalized_name": line.lower().strip(),
                            "context": f"Email signature: {signature[:100]}",
                            "confidence": 0.6,
                            "attributes": {},
                        })

        return people

    def _extract_from_emails(self, text: str) -> List[Dict]:
        """Extract people from email addresses"""
        people = []

        emails = re.findall(self.EMAIL_PATTERN, text)

        for email_addr in emails:
            # Try to extract name from email (e.g., john.smith@example.com -> John Smith)
            local_part = email_addr.split("@")[0]

            if "." in local_part:
                parts = local_part.split(".")
                name = " ".join(p.capitalize() for p in parts)

                people.append({
                    "name": name,
                    "normalized_name": name.lower(),
                    "context": f"Email address: {email_addr}",
                    "confidence": 0.5,
                    "attributes": {"email": email_addr},
                })

        return people

    def _extract_from_domains(self, text: str) -> List[Dict]:
        """Extract companies from email domains"""
        companies = []

        emails = re.findall(self.EMAIL_PATTERN, text)

        for email_addr in emails:
            domain = email_addr.split("@")[1]

            # Skip common email providers
            if domain.lower() in ["gmail.com", "yahoo.com", "outlook.com", "hotmail.com"]:
                continue

            # Extract company name from domain (example.com -> Example)
            company_name = domain.split(".")[0].capitalize()

            companies.append({
                "name": company_name,
                "normalized_name": company_name.lower(),
                "context": f"Email domain: {domain}",
                "confidence": 0.6,
                "attributes": {"domain": domain},
            })

        return companies

    def _parse_currency(self, amount_str: str) -> Tuple[str, float]:
        """
        Parse currency symbol and value from amount string

        Returns:
            Tuple of (currency_code, float_value)
        """
        # Remove spaces
        amount_str = amount_str.strip()

        # Detect currency
        currency = "USD"  # Default

        if "€" in amount_str or "EUR" in amount_str.upper():
            currency = "EUR"
        elif "£" in amount_str or "GBP" in amount_str.upper():
            currency = "GBP"
        elif "₹" in amount_str or "INR" in amount_str.upper():
            currency = "INR"

        # Extract numeric value
        numeric_str = re.sub(r'[^\d.]', '', amount_str)

        try:
            value = float(numeric_str)
        except ValueError:
            value = 0.0

        return currency, value

    def _deduplicate_entities(self, entities: List[Dict]) -> List[Dict]:
        """
        Deduplicate entities by normalized name

        Args:
            entities: List of entity dictionaries

        Returns:
            Deduplicated list
        """
        seen = {}

        for entity in entities:
            norm_name = entity["normalized_name"]

            if norm_name not in seen:
                seen[norm_name] = entity
            else:
                # Keep entity with higher confidence
                if entity["confidence"] > seen[norm_name]["confidence"]:
                    seen[norm_name] = entity

        return list(seen.values())
