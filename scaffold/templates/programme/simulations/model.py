"""Deterministic case function for this programme.

Replace run_case before relying on an execution record. This stub raises so an
empty programme cannot be mistaken for an executed result. It does not set
authorization_status and it does not award programme credit.
"""


def run_case(case):
    raise NotImplementedError(
        "simulations/model.py has no case function yet. "
        "Author the expected outcome in simulations/scenarios.json before execution. "
        "This stub does not produce evidence."
    )
