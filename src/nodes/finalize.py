"""Finalize node: set the terminal status and print a summary report."""
from __future__ import annotations


def finalize_node(state: dict) -> dict:
    validation = state.get("validation") or {}
    critique = state.get("critique") or {}
    success = bool(validation.get("passed")) and bool(critique.get("matches"))
    status = "success" if success else "failed"

    print("\n" + "=" * 60)
    print(f"RESULT: {status.upper()}  (after {state.get('iteration', 0)} iteration(s))")
    print("-" * 60)
    if validation:
        print(f"  watertight        : {validation.get('is_watertight')}")
        print(f"  winding_consistent: {validation.get('is_winding_consistent')}")
        print(f"  euler_number      : {validation.get('euler_number')} "
              f"(expected {validation.get('expected_euler')})")
        print(f"  dims_ok           : {validation.get('dims_ok')}")
        print(f"  volume            : {validation.get('volume')}")
    if critique:
        print(f"  visual_match      : {critique.get('matches')}")
    if not success and state.get("feedback"):
        print(f"  last feedback     : {state['feedback'][:200]}")
    print("=" * 60 + "\n")
    return {"status": status}
