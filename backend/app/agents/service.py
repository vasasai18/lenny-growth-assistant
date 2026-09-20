from collections.abc import Sequence
import logging

from app.agents.lenny_agent import AgentMode, AgentResult, ClaudeAgentRunner, LocalAgentRunner
from app.config import Settings, get_settings
from app.providers import ChatMessage, ProviderResponseError, create_provider


logger = logging.getLogger(__name__)


class AgentService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def run(
        self,
        provider_name: str,
        user_message: str,
        mode: AgentMode,
        history: Sequence[ChatMessage],
    ) -> AgentResult:
        if provider_name == "anthropic":
            try:
                return await ClaudeAgentRunner(self.settings).run(
                    user_message, mode=mode, history=history
                )
            except ProviderResponseError as exc:
                logger.warning(
                    "claude_agent_sdk_fallback",
                    extra={"sdk_error": str(exc), "mode": mode},
                )
                provider = create_provider("anthropic", self.settings)
                return await LocalAgentRunner(self.settings, provider).run(
                    user_message, mode=mode, history=history
                )
        provider = create_provider("ollama", self.settings)
        return await LocalAgentRunner(self.settings, provider).run(
            user_message, mode=mode, history=history
        )


def get_agent_service() -> AgentService:
    return AgentService(get_settings())
