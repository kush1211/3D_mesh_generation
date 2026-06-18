"""Plan node: Gemini looks at the image and returns a structured build plan."""
from __future__ import annotations

from langchain_core.messages import HumanMessage, SystemMessage

from ..llm.models import build_chat_model
from ..llm.prompts import PLAN_PROMPT, PLAN_SYSTEM
from ..llm.schemas import Plan
from .stubs import STUB_PLAN


async def plan_node(state: dict) -> dict:
    if state.get("stub"):
        print("[plan] (stub) using canned plan")
        return {"plan": STUB_PLAN}

    model = build_chat_model().with_structured_output(Plan)
    image_block = {
        "type": "image_url",
        "image_url": {
            "url": f"data:{state['image_mime']};base64,{state['image_b64']}"
        },
    }
    messages = [
        SystemMessage(content=PLAN_SYSTEM),
        HumanMessage(content=[{"type": "text", "text": PLAN_PROMPT}, image_block]),
    ]
    plan: Plan = await model.ainvoke(messages)
    plan_dict = plan.model_dump()
    print(f"[plan] {plan_dict['object_type']} via {plan_dict['operations']} "
          f"(euler={plan_dict['expected_euler']})")
    return {"plan": plan_dict}
