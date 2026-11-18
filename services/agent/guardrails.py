"""
Security Guardrails & Prompt Injection Defense for SiteSense.
Protects the platform against adversarial prompts planted in uploaded PDFs,
scanned signage text, and user inputs.
"""

import re
from typing import Tuple, Optional

# Known adversarial jailbreak & injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|prior\s+|previous\s+)?instructions",
    r"override\s+(all\s+)?safety\s+(rules|protocols|checks)",
    r"pass\s+(all\s+)?inspections?\s+unconditionally",
    r"delete\s+all\s+(findings|inspections|tables|records)",
    r"system\s+prompt\s+leak",
    r"reveal\s+(your\s+)?(system\s+instructions|secret|api\s+keys)",
    r"grant\s+(me\s+)?admin\s+access",
    r"by\s+order\s+of\s+osha,\s+ignore",
    r"disregard\s+prior\s+guidelines",
    r";\s*(drop|delete|truncate|alter)\s+table"
]


class SecurityGuardrails:
    """
    Validates user queries and untrusted OCR/document text against malicious payloads.
    """

    def __init__(self):
        self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def validate_input(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Scans input string for prompt injection or malicious instructions.
        Returns:
            (is_safe: bool, violation_reason: Optional[str])
        """
        if not text:
            return True, None

        for pattern in self._compiled_patterns:
            match = pattern.search(text)
            if match:
                matched_phrase = match.group(0)
                return False, f"Malicious payload blocked: Adversarial injection detected ('{matched_phrase}')."

        return True, None

    def sanitize_untrusted_text(self, text: str) -> str:
        """
        Sanitizes text extracted from third-party documents before injection into agent context.
        Neutralizes command syntax and escape delimiters.
        """
        # Neutralize common markdown/prompt injection brackets
        sanitized = re.sub(r"\[(SYSTEM|DEVELOPER|AGENT|ADMIN)\]", "[FILTERED_TAG]", text, flags=re.IGNORECASE)
        # Neutralize delimiter breaks
        sanitized = sanitized.replace("```", "'''").replace("---", "___")
        return sanitized

