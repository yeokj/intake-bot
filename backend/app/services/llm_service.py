import json
from typing import List, Tuple
from app.core.config import settings
from app.core.prompts import SYSTEM_INTAKE_PROMPT, BRIEF_GENERATION_PROMPT
from app.models.chat import ChatMessage
from app.models.brief import ProjectBrief

# Mock conversation script to simulate adaptive client intake without API keys
MOCK_INTAKE_SCRIPT = [
    "Welcome to the Tech Incubator at Queens College (TIQC)! I'm here to learn about your project so our team can prepare a tailored scope. To get started, could you tell me a bit about your business or organization?",
    "Thanks for sharing! Do you currently have an existing website or application in place, or are you looking to build something entirely from scratch?",
    "Got it. What are the key features or primary goals you need this new solution to achieve? For instance, do you need user logins, payments, or specific integrations?",
    "Understood. Lastly, what rough launch timeline are you targeting, and do you have a ballpark budget tier in mind? Don't worry if you're not 100% sure—our team can help refine this. [INTAKE_COMPLETE]"
]


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.api_key = settings.OPENAI_API_KEY

    async def get_next_response(self, messages: List[ChatMessage]) -> Tuple[str, bool]:
        """
        Takes conversation history, calls LLM (or mock engine),
        and returns (assistant_text, is_intake_complete).
        """
        # Count user messages to track progress in mock mode
        user_message_count = sum(1 for m in messages if m.role == "user")

        if self.provider == "mock" or not self.api_key:
            # Step through simulated questions
            idx = min(user_message_count, len(MOCK_INTAKE_SCRIPT) - 1)
            response_text = MOCK_INTAKE_SCRIPT[idx]
            is_complete = "[INTAKE_COMPLETE]" in response_text
            cleaned_text = response_text.replace("[INTAKE_COMPLETE]", "").strip()
            return cleaned_text, is_complete

        # Live OpenAI integration
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            formatted_messages = [{"role": "system", "content": SYSTEM_INTAKE_PROMPT}]
            for msg in messages:
                formatted_messages.append({"role": msg.role, "content": msg.content})

            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=formatted_messages,
                temperature=0.7,
            )

            raw_content = response.choices[0].message.content or ""
            is_complete = "[INTAKE_COMPLETE]" in raw_content
            cleaned_content = raw_content.replace("[INTAKE_COMPLETE]", "").strip()
            return cleaned_content, is_complete

        except Exception as e:
            # Fallback gracefully
            return f"Thank you for that information. Our technical scoping team will review this shortly. [Error: {str(e)}]", False

    async def generate_brief(self, messages: List[ChatMessage]) -> ProjectBrief:
        """
        Extracts structured ProjectBrief from full chat transcript.
        """
        transcript = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages])

        if self.provider == "mock" or not self.api_key:
            # Return realistic mock brief for testing
            return ProjectBrief(
                client_name_or_business="Mock Queens Startup LLC",
                business_type="Local B2B Logistics / Service Marketplace",
                current_situation="Has a legacy WordPress landing page, but no booking or customer portal.",
                goals_and_needs=[
                    "Custom client portal with authentication",
                    "Online booking and appointment calendar",
                    "Automated email notifications via SendGrid"
                ],
                suggested_service_category="Custom Web Application Development",
                rough_budget_range="$5,000 - $10,000",
                target_timeline="Q3 Launch (within 3 months)",
                flagged_unknowns=[
                    "Need clarification on whether payment processing (Stripe) is required in v1.",
                    "Clarify who provides design assets/wireframes."
                ]
            )

        # Live structured extraction
        try:
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=self.api_key)

            response = await client.beta.chat.completions.parse(
                model=settings.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": BRIEF_GENERATION_PROMPT},
                    {"role": "user", "content": f"Intake Transcript:\n{transcript}"}
                ],
                response_format=ProjectBrief,
                temperature=0.2,
            )
            return response.choices[0].message.parsed
        except Exception as e:
            # Fallback generic brief if parsing fails
            return ProjectBrief(
                client_name_or_business="Client from Chat",
                business_type="General Inquiry",
                current_situation="Review chat transcript for details",
                goals_and_needs=["Extracted from chat"],
                suggested_service_category="Technical Consulting & System Architecture",
                rough_budget_range="TBD on call",
                target_timeline="TBD on call",
                flagged_unknowns=[f"Auto-extraction error: {str(e)}"]
            )


llm_service = LLMService()