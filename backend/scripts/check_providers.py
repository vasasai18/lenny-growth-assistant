import asyncio

from app.providers import ChatMessage, ProviderError, create_provider


async def main() -> None:
    local = create_provider("ollama")
    response = await local.generate(
        [
            ChatMessage(
                role="user",
                content="Reply exactly: Provider switching is ready.",
            )
        ],
        "Follow the user's formatting instruction and answer briefly.",
        temperature=0,
        max_tokens=30,
    )
    print(f"Selected provider: {local.name}")
    print(f"Selected model: {local.model}")
    print(f"Response: {response}")

    try:
        create_provider("anthropic")
    except ProviderError as exc:
        print(f"Unconfigured cloud check: PASS ({exc.code})")
    else:
        print("Cloud provider is configured; missing-key check skipped.")

    print("Provider abstraction: PASS")


if __name__ == "__main__":
    asyncio.run(main())

