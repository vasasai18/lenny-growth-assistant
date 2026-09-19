import asyncio

from app.agents.lenny_agent import LocalAgentRunner
from app.config import get_settings
from app.database import close_database
from app.providers import create_provider


async def main() -> None:
    settings = get_settings()
    provider = create_provider("ollama", settings)
    agent = LocalAgentRunner(settings, provider)
    try:
        result = await agent.run(
            "According to the transcripts, how should product teams decide what to build?"
        )

        print(f"Provider: {result.provider}")
        print(f"Model: {result.model}")
        print(f"Sources returned: {len(result.sources)}")
        for source in result.sources:
            print(
                f"[{source['citation_number']}] {source['episode_title']} "
                f"({source['timestamp_ref']})"
            )
        print("\nGrounded response:")
        print(result.content)
        print("\nLocal agent route: PASS")
    finally:
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())
