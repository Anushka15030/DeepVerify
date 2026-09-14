import asyncio

from app.services.graph_runner import run_research


async def main():
    question = "What are the major challenges of AI fact-checking systems?"

    print("\nStarting DeepVerify real E2E run...")
    print(f"Question: {question}\n")

    state = await run_research(question)

    print("\n" + "=" * 60)
    print("FINAL RESULT")
    print("=" * 60)

    print(f"\nRun ID: {state.run_id}")
    print(f"Grounding score: {state.grounding_score}")
    print(f"Revision count: {state.revision_count}")

    print(f"\nEvidence groups: {len(state.evidence)}")
    print(f"Claims: {len(state.claims)}")
    print(f"Claim checks: {len(state.claim_checks)}")

    print("\n--- EVENTS ---")
    for event in state.agent_events:
        print(f"{event.type}")

    if state.errors:
        print("\n--- ERRORS ---")
        for key, value in state.errors.items():
            print(f"{key}: {value}")

    print("\n--- DRAFT ---")
    print(state.draft or "NO DRAFT")


if __name__ == "__main__":
    asyncio.run(main())