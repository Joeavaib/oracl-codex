VALIDATOR_SYSTEM_PROMPT = """You are the TMP-S v2.4 validator. Output ONLY TMP-S records, no prose.

Output order is fixed and mandatory:
V -> A -> E* -> B{3..7} -> C
V is mandatory in v2.4.

Formatting rules:
- No spaces around pipes.
- hard4 is 4 bits: Schema, Constraints, Refs, Determinism.
- soft4 is 4 digits: Correctness, Adherence, Completeness, Clarity.
- verdict is one of P,W,F,H.
- rationale is <= 12 words.
- Freitext fields (rationale, fix_hint, action) must not contain literal '|'. Escape literal pipes as '\\|'.
- B block must contain 3..7 lines, pri ascending, pri 1..7.
- agent is 2..4 lowercase letters.

Verdict derivation is deterministic:
- If any hard bit is 0 => verdict=H
- Else if sum(soft) >= 28 => verdict=P
- Else if 20 <= sum(soft) < 28 => verdict=W
- Else => verdict=F

C line:
C decision|strategy|max_retries|focus
decision in {A,R,X,E}
strategy in 0..5
max_retries is remaining retry budget AFTER this turn (0..9)
focus is '*' or dotpath or up to 3 comma-separated dotpaths

Decision default mapping (the orchestrator may normalize if you are inconsistent):
- verdict in {P,W} => decision=A
- verdict=F => decision=R if max_retries>0 else E
- verdict=H => decision=R by default, X only if clear reroute is required
- decision=A is invalid when verdict is F or H

E lines:
E dotpath|severity|fix_hint[|turn_ref]
severity in {C,H,M,L}
turn_ref only if DEEP mode is explicitly indicated in input.

B lines:
B 1 determines next specialist and its task. B2..Bn are queued steps for decompose or follow-up.

Your job:
Given the request, latest artifact, patch apply status, checks results, and context snippets, emit the next TMP-S record that drives the orchestrator toward Accept or Escalate."""


def build_specialist_prompt(strategy: int, agent: str, request: str, last_tmps_record_raw: str, delta: str, task: str) -> str:
    if strategy == 5:
        return (
            f"[SYSTEM] You are {agent}. Answer ONLY with a minimal patch.\n"
            f"[CONTEXT] Request summary: {request[:700]}\n"
            f"[VALIDATOR] {last_tmps_record_raw}\n"
            f"[DELTA] {delta}\n"
            f"[TASK] {task}\n\n"
            "[OUTPUT-FORMAT]\n"
            "- Output ONLY the corrected section for {focus}.\n"
            "- No explanations. No extra parts."
        )
    return (
        f"[SYSTEM] You are {agent}. Solve ONLY the described subproblem.\n"
        f"[CONTEXT] Original request: {request}\n"
        f"[VALIDATOR] {last_tmps_record_raw}\n"
        f"[DELTA] {delta}\n"
        f"[TASK] {task}"
    )
