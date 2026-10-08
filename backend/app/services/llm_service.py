import json
import re
from typing import List, Tuple
from app.core.config import settings
from app.core.prompts import SYSTEM_INTAKE_PROMPT, BRIEF_GENERATION_PROMPT
from app.models.chat import ChatMessage
from app.models.brief import ProjectBrief


class LLMService:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.api_key = settings.OPENAI_API_KEY

    def _smart_mock_response(self, messages: List[ChatMessage]) -> Tuple[str, bool]:
        """
        Universal fallback engine with adaptive turn progression:
        - Turn 1: Inspects platform/concept/URL -> Drills into pain points & tech stack.
        - Turn 2: Inspects features/integrations -> If no budget/timeline mentioned, asks for timeline & budget.
        - Turn 3+: Once budget/timeline are provided, wraps up with [INTAKE_COMPLETE].
        """
        user_msgs = [m.content for m in messages if m.role == "user"]
        user_count = len(user_msgs)
        last_msg = user_msgs[-1] if user_msgs else ""
        last_lower = last_msg.lower()
        full_text = " ".join(user_msgs).lower()

        # Check for URL
        url_match = re.search(r'(https?://\S+|www\.\S+|\b\w+\.(?:com|org|io|co|net|dev|ai)\b)', last_msg, re.IGNORECASE)
        found_url = url_match.group(0) if url_match else None

        # Check if the user already provided timeline or budget signals
        has_budget_or_timeline = any(k in full_text for k in [
            "month", "week", "season", "$", "budget", "000", "timeline", "launch", " k "
        ])

        # --- TURN 1: Drill into Current State / Pain Points ---
        if user_count == 1:
            if found_url:
                return (
                    f"Thanks for sharing your link ({found_url})! To help TIQC scope this accurately: "
                    "What are the biggest technical limitations or pain points with the current site, "
                    "and are you looking for a visual refresh or a complete architectural overhaul?",
                    False
                )
            if "shopify" in last_lower:
                return (
                    "Thanks for reaching out! Since you're already on Shopify, let's look at what's hurting conversions: "
                    "Are you experiencing high checkout abandonment, slow page load times, or a cluttered mobile experience? "
                    "And are you currently using an off-the-shelf theme or custom code?",
                    False
                )
            if any(k in last_lower for k in ["store", "ecommerce", "e-commerce", "selling"]):
                return (
                    "Thanks for reaching out! For your e-commerce operations: What platform are you currently running on "
                    "(e.g., Shopify, WooCommerce, or custom), and what specific bottlenecks are you facing with sales or inventory?",
                    False
                )
            if any(k in last_lower for k in ["app", "ios", "android", "mobile"]):
                return (
                    "Exciting project! For your mobile application: Are you targeting iOS, Android, or cross-platform? "
                    "And do you already have UI/UX wireframes designed, or will this build start from scratch?",
                    False
                )
            if any(k in last_lower for k in ["ai", "machine learning", "llm", "automation", "saas", "dashboard"]):
                return (
                    "That sounds like a promising software initiative. What are the core user workflows for this platform? "
                    "For example, will this require user authentication, specific API integrations, or real-time data processing?",
                    False
                )
            if any(k in last_lower for k in ["wordpress", "wix", "squarespace", "redesign"]):
                return (
                    "Understood. For your existing site, what tech stack or CMS is it currently running on, "
                    "and where are you hitting a wall—performance, design modernness, or feature limitations?",
                    False
                )
            return (
                "Welcome to TIQC! To help our technical advisors understand your vision: "
                "Could you tell me a bit more about your target audience, and whether you already have an existing "
                "system/codebase in place or are starting completely from the ground up?",
                False
            )

        # --- TURN 2: Features, Integrations & Sizing ---
        if user_count == 2:
            # If the user already provided budget/timeline in turn 1 or 2, we can conclude
            if has_budget_or_timeline:
                return (
                    "Thank you for sharing your project goals and timeframe! I have synthesized everything "
                    "into a preliminary project brief for our TIQC technical scoping team. An advisor will review "
                    "your requirements and reach out to schedule your discovery call. [INTAKE_COMPLETE]",
                    True
                )
            
            # If they discussed Shopify/Ecommerce features, acknowledge them and ask for timeline & budget
            if any(k in full_text for k in ["shopify", "ecommerce", "store"]):
                return (
                    "That provides a clear picture: upgrading to a lightweight theme to resolve mobile latency, "
                    "cleaning up conflicting apps, and setting up automated Klaviyo flows plus inventory sync. "
                    "To help our TIQC team scope the appropriate engineering milestones: "
                    "What is your target launch timeline, and do you have a ballpark budget range in mind?",
                    False
                )
            
            # Default for other archetypes
            return (
                "Understood. To help our incubator advisors size the initial phase and recommend the right team: "
                "What is your target launch window, and do you have an approximate budget tier in mind? "
                "(Don't worry if you don't have an exact figure—a rough range is fine).",
                False
            )

        # --- TURN 3+: Wrap-up and Completion Trigger ---
        return (
            "Thank you so much for providing all these details! I have synthesized everything into a preliminary "
            "project brief for our TIQC technical scoping team. An advisor will review your requirements and reach out "
            "to schedule your discovery call. [INTAKE_COMPLETE]",
            True
        )

    async def get_next_response(self, messages: List[ChatMessage]) -> Tuple[str, bool]:
        """
        Takes conversation history, calls live LLM (or universal fallback engine),
        and returns (assistant_text, is_intake_complete).
        """
        if self.provider == "mock" or not self.api_key:
            return self._smart_mock_response(messages)

        # Live OpenAI integration (handles arbitrary, highly complex client conversations)
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
            return f"Thank you for that context. [Error connecting to provider: {str(e)}]", False

    async def generate_brief(self, messages: List[ChatMessage]) -> ProjectBrief:
        """
        Extracts structured ProjectBrief from full chat transcript.
        """
        transcript = "\n".join([f"{m.role.upper()}: {m.content}" for m in messages])
        transcript_lower = transcript.lower()

        if self.provider == "mock" or not self.api_key:
            # Determine domain dynamically
            if any(k in transcript_lower for k in ["shopify", "store", "ecommerce"]):
                category = "E-commerce & Transactional Platform"
                biz_name = "E-Commerce Prospect"
                situation = "Has an active digital storefront seeking conversion and custom app enhancements."
                goals = ["Platform optimization", "Custom third-party integrations", "Checkout and inventory enhancements"]
            elif any(k in transcript_lower for k in ["app", "ios", "android", "mobile"]):
                category = "MVP Build for Startups"
                biz_name = "Mobile App Startup"
                situation = "Early-stage mobile concept requiring cross-platform MVP development."
                goals = ["User onboarding & authentication", "Native device capabilities", "Scalable backend API"]
            elif any(k in transcript_lower for k in ["ai", "saas", "automation", "dashboard"]):
                category = "Custom Web Application Development"
                biz_name = "SaaS / AI Venture"
                situation = "Developing proprietary software tool requiring custom architecture and user flows."
                goals = ["Multi-tenant portal", "API integrations and automated pipelines", "Admin analytics dashboard"]
            elif any(k in transcript_lower for k in ["wordpress", "redesign", "wix", "squarespace"]):
                category = "Website Redesign / Modernization"
                biz_name = "Established Business Refresh"
                situation = "Outdated legacy website experiencing performance or layout bottlenecks."
                goals = ["Modern UI/UX redesign", "Mobile responsive performance", "Simplified content management"]
            else:
                category = "Technical Consulting & System Architecture"
                biz_name = "Prospective Venture"
                situation = "New project concept in exploratory technical discovery."
                goals = ["Technical scoping and requirements gathering", "Architecture recommendation"]

            return ProjectBrief(
                client_name_or_business=biz_name,
                business_type="Prospective Incubator Client",
                current_situation=situation,
                goals_and_needs=goals,
                suggested_service_category=category,
                rough_budget_range="$5,000 - $15,000 (Ballpark)",
                target_timeline="Targeting 2-3 months",
                flagged_unknowns=[
                    "Validate exact technical dependencies and external APIs on initial discovery call.",
                    "Confirm wireframe and design asset readiness before scoping sprint."
                ]
            )

        # Live structured extraction via OpenAI
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