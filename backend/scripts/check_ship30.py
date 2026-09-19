import argparse
import asyncio
import json
from pathlib import Path

from app.agents.lenny_agent import LocalAgentRunner
from app.config import get_settings
from app.database import close_database
from app.providers import create_provider
from app.skills.ship30_writer import Ship30Writer


async def run(topic: str, output: Path | None = None) -> None:
    settings = get_settings()
    agent = LocalAgentRunner(settings, create_provider("ollama", settings))
    try:
        result = await agent.run(topic, mode="ship30")
        validation = Ship30Writer.validate(result.content, len(result.sources))
        print(result.content)
        print("\n--- VALIDATION ---")
        print(f"Sources: {len(result.sources)}")
        print(f"Words: {validation.word_count}")
        print(f"Valid: {validation.valid}")
        for error in validation.errors:
            print(f"- {error}")
        if output is not None:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(result.content, encoding="utf-8")
            report_path = output.with_suffix(".validation.json")
            report_path.write_text(
                json.dumps(
                    {
                        "sources": len(result.sources),
                        "word_count": validation.word_count,
                        "valid": validation.valid,
                        "errors": list(validation.errors),
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(f"Essay saved to: {output}")
            print(f"Validation saved to: {report_path}")
    finally:
        await close_database()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate and validate a local Ship 30 essay.")
    parser.add_argument(
        "topic",
        nargs="?",
        default="How product teams can decide what to build through small experiments",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    asyncio.run(run(args.topic, args.output))


if __name__ == "__main__":
    main()
