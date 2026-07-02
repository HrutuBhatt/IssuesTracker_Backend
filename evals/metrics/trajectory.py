"""Trajectory eval — checks the sequence of tool calls the agent made."""


def check_trajectory(actual: list[dict], rules: dict) -> tuple[bool, str]:
    """
    actual: list of {"name": str, "args": dict} — one entry per tool call in order.

    rules keys (all optional):
      must_contain:      list[str]             — tool names that must appear at least once
      must_not_contain:  list[str]             — tool names that must not appear
      must_precede:      list[tuple[str,str]]  — (A, B): A must appear before B
      exact_count:       dict[str, int]        — tool must appear exactly N times
      must_contain_args: list[dict]            — {tool, arg, value}: tool must have been
                                                 called with args[arg] == value at least once
    """
    names = [c["name"] for c in actual]
    failures = []

    for tool in rules.get("must_contain", []):
        if tool not in names:
            failures.append(f"'{tool}' was not called but should have been")

    for tool in rules.get("must_not_contain", []):
        if tool in names:
            failures.append(f"'{tool}' was called but should not have been")

    for a, b in rules.get("must_precede", []):
        if a in names and b in names:
            if names.index(a) > names.index(b):
                failures.append(f"'{a}' must be called before '{b}' but was not")
        elif b in names and a not in names:
            failures.append(f"'{a}' must be called before '{b}' but '{a}' was never called")

    for tool, expected_count in rules.get("exact_count", {}).items():
        actual_count = names.count(tool)
        if actual_count != expected_count:
            failures.append(f"'{tool}' expected exactly {expected_count} call(s), got {actual_count}")

    for spec in rules.get("must_contain_args", []):
        tool, arg, expected_val = spec["tool"], spec["arg"], spec["value"]
        matching_calls = [c for c in actual if c["name"] == tool]
        if not matching_calls:
            failures.append(f"'{tool}' was never called (needed for arg check '{arg}'={expected_val!r})")
        elif not any(c["args"].get(arg) == expected_val for c in matching_calls):
            actual_vals = [c["args"].get(arg) for c in matching_calls]
            failures.append(f"'{tool}' was called but never with {arg}={expected_val!r} (got {actual_vals})")

    if failures:
        return False, " | ".join(failures)
    return True, "ok"
