import os
import logging
from typing import Optional
from dotenv import load_dotenv

# Import as requested by user's example
try:
    from agents import Agent, AsyncOpenAI, OpenAIChatCompletionsModel, Runner # type: ignore
    from agents.run import RunConfig # type: ignore
except ImportError:
    # Fallback to standard openai if agents is not available, 
    # but we will try to follow the user's provided structure.
    from openai import AsyncOpenAI
    Agent = None
    OpenAIChatCompletionsModel = None
    Runner = None
    RunConfig = None

load_dotenv()
logger = logging.getLogger(__name__)

class EmailAIAgent:
    def __init__(self):
        # API Keys from env
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.grok_api_key = os.getenv("GROK_API_KEY")
        
        # System instructions
        self.instructions = (
            "You are Yaram Kazmi, a helpful AI assistant and always appreciate on good things or user or motivate him/her. "
            "Your owner is Areeba Zafar and your name is Yaram Kazmi. "
            "Write polite, professional, and motivating emails. Keep them concise but effective."
        )

    def _get_gemini_config(self):
        if not self.gemini_api_key:
            return None
        
        external_client = AsyncOpenAI(
            api_key=self.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
        
        if OpenAIChatCompletionsModel:
            model = OpenAIChatCompletionsModel(
                model="gemini-2.5-flash",
                openai_client=external_client
            )
            return RunConfig(
                model=model,
                model_provider=external_client,
                tracing_disabled=True
            )
        return None

    def _get_grok_config(self):
        if not self.grok_api_key:
            return None
        
        external_client = AsyncOpenAI(
            api_key=self.grok_api_key,
            base_url="https://api.x.ai/v1/"
        )
        
        if OpenAIChatCompletionsModel:
            model = OpenAIChatCompletionsModel(
                model="grok-2",
                openai_client=external_client
            )
            return RunConfig(
                model=model,
                model_provider=external_client,
                tracing_disabled=True
            )
        return None

    async def generate_content(self, user_prompt: str) -> str:
        """Tries Gemini first, falls back to Grok if Gemini fails."""
        
        # 1. Try Gemini (Primary)
        config = self._get_gemini_config()
        if config and Runner:
            try:
                logger.info("Generating content using Gemini (Primary) via agents SDK...")
                agent = Agent(name="Yaram Kazmi", instructions=self.instructions)
                # Note: Runner.run_sync is used in user example, but we are in async context.
                # If Runner has an async version, we'd use it. User example showed run_sync.
                result = Runner.run_sync(agent, user_prompt, run_config=config)
                return result.final_output
            except Exception as e:
                logger.warning(f"Gemini agents call failed: {e}. Falling back to Grok...")

        # 2. Try Grok (Fallback)
        config = self._get_grok_config()
        if config and Runner:
            try:
                logger.info("Generating content using Grok (Fallback) via agents SDK...")
                agent = Agent(name="Yaram Kazmi", instructions=self.instructions)
                result = Runner.run_sync(agent, user_prompt, run_config=config)
                return result.final_output
            except Exception as e:
                logger.error(f"Grok agents fallback call failed: {e}")

        # 3. Last resort: Standard OpenAI call if SDK fails
        logger.info("Falling back to standard OpenAI API call...")
        client = AsyncOpenAI(api_key=self.gemini_api_key or self.grok_api_key, 
                             base_url="https://generativelanguage.googleapis.com/v1beta/openai/" if self.gemini_api_key else "https://api.x.ai/v1/")
        model = "gemini-2.5-flash" if self.gemini_api_key else "grok-2"
        
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": self.instructions},
                    {"role": "user", "content": user_prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Final fallback failed: {e}")
            raise Exception("All AI generation attempts failed. Check your API keys and SDK installation.")

    async def draft_email_reply(self, original_email: str, sender: str, instructions: str) -> str:
        user_prompt = f"Original Email from {sender}:\n{original_email}\n\nUser Instructions for reply: {instructions}"
        return await self.generate_content(user_prompt)

    async def draft_new_email(self, topic: str, recipient: str) -> str:
        user_prompt = f"Write a new email to {recipient} about the following topic: {topic}"
        return await self.generate_content(user_prompt)

ai_agent = EmailAIAgent()
