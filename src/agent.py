"""The asset review agent: tool descriptions and the agent loop."""

import json
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

from src.tools import (
    VALID_STATUSES,
    REVIEW_DATE,
    get_asset,
    get_dependencies,
    get_dependents,
    list_assets,
)

# ************************** Tools' Description **************************
TOOLS: list = [
    {
        "type": "function",
        "name": "list_assets",
        "description": (
            "List every asset in Kosha Bank's software inventory as short summaries: "
            "ID, name, version, business criticality, data sensitivity, and support status. "
            "Call with no filter to see the whole inventory in one call. "
            "Use this first when asked which assets need review, or to find an asset's ID by name."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "support_status": {
                    "type": "string",
                    "enum": [s for s in VALID_STATUSES if s != "unknown"],
                    "description": "Only return assets with this support status.",
                }
            },
            "required": [],
        },
    },
    {
        "type": "function",
        "name": "get_asset",
        "description": (
            "Get the full record for one asset by ID, including annual maintenance cost "
            "(null means not recorded, 0 means no cost), end of support date, source URL, "
            "support status, and days until end of support (negative means already past). "
            "For saas and in_house assets the date and source are always empty because no "
            "vendor lifecycle exists; this is expected, not missing data. "
            "Returns an error if the ID does not exist."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID such as A05."}
            },
            "required": ["asset_id"],
        },
    },
    {
        "type": "function",
        "name": "get_dependencies",
        "description": (
            "List the assets this asset depends on, each with its support status. "
            "One level only; call again on a result to go deeper."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID such as A14."}
            },
            "required": ["asset_id"],
        },
    },
    {
        "type": "function",
        "name": "get_dependents",
        "description": (
            "List the assets that depend on this asset, each with its support status. "
            "Shows what would be affected if this asset failed or were retired. "
            "One level only; call again on a result to go deeper."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "asset_id": {"type": "string", "description": "Asset ID such as A02."}
            },
            "required": ["asset_id"],
        },
    },
]

TOOL_FUNCTIONS = {
    "list_assets": list_assets,
    "get_asset": get_asset,
    "get_dependencies": get_dependencies,
    "get_dependents": get_dependents,
}

# ************************** Tools' Description **************************

SYSTEM_PROMPT = f"""You are an IT asset review assistant for Kosha Bank, a fictional mid-size private bank.
A technology manager will ask about the bank's software inventory. Use the tools to look up facts.
Never state a fact about an asset that you did not get from a tool in this conversation.

For each asset you assess, propose one of:
- maintain: supported, no action needed now
- replace: support has ended or is ending soon, and the evidence supports planning a replacement
- investigate: important information is missing or the evidence is mixed, so a person needs to look closer

Rules:
- Cite asset IDs (for example A05) for every claim.
- To find an asset by name, call list_assets once with no filter.
- Check dependencies when they could change the answer, such as for in-house applications, which have no vendor support date, or infrastructure that other systems run on.
- If information you need is missing, say exactly what is missing and recommend investigate rather than guessing.
- If a tool returns an error, report it plainly. Do not invent results.
- Your recommendations are proposals for human review, not decisions. Do not repeat this in your answer.

Answer format. Plain text only, no markdown, no introduction, no closing summary.
For each asset you assess, write one block of at most 60 words:
<asset ID> <product name>: <maintain | replace | investigate>
Why: one or two sentences.
Evidence: the asset IDs and specific facts you relied on, for example "A05 end of support 2024-07-09".
Next step: one sentence.

Support status is measured on the review date {REVIEW_DATE}. ending_soon means within the next 24 months.
not_applicable means SaaS or in-house software with no vendor lifecycle.
"""

MAX_STEPS = 10

load_dotenv()
client = OpenAI()
MODEL = os.getenv("OPENAI_MODEL", "gpt-6-luna")


def run_tool(name, arguments_json):
    """Run one tool the model asked for. Errors become results, not crashes."""
    if name not in TOOL_FUNCTIONS:
        return {"error": "unknown_tool", "tool": name}
    try:
        arguments = json.loads(arguments_json or "{}")
        return TOOL_FUNCTIONS[name](**arguments)
    except Exception as exc:
        return {"error": "tool_failed", "tool": name, "detail": str(exc)}


def run_agent(question):
    """Answer one question, letting the model choose which tools to call."""
    print(f"\nQUESTION: {question}\nMODEL: {MODEL}\n")
    conversation: list = [{"role": "user", "content": question}]

    for step in range(1, MAX_STEPS + 1):
        response = client.responses.create(
            model=MODEL,
            instructions=SYSTEM_PROMPT,
            input=conversation,
            tools=TOOLS,
        )

        tool_calls = [item for item in response.output if item.type == "function_call"]

        if not tool_calls:
            print(f"FINAL ANSWER (after {step - 1} tool steps):\n")
            print(response.output_text)
            return response.output_text

        conversation += response.output

        for call in tool_calls:
            print(f"STEP {step}: model chose {call.name}({call.arguments})")
            result = run_tool(call.name, call.arguments)
            preview = json.dumps(result)
            print(f"  RESULT: {preview[:150]}{'...' if len(preview) > 150 else ''}\n")
            conversation.append({
                "type": "function_call_output",
                "call_id": call.call_id,
                "output": json.dumps(result),
            })

    print("STOPPED: step limit reached without a final answer.")
    return None


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or input("Question: ")
    run_agent(question)