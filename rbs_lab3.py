import json
import operator
from typing import Any, Dict, List, Tuple
import streamlit as st

# ----------------------------
# 1) Rule Engine Core Logic
# ----------------------------
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "in": lambda a, b: a in b,
    "not_in": lambda a, b: a not in b,
}

# Exact default rules required by Question 2
DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0],
        ],
        "action": {
            "decision": "AWARD FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need",
        },
    },
    {
        "name": "Low CGPA not eligible",
        "priority": 95,
        "conditions": [["cgpa", "<", 2.5]],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement",
        },
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [["disciplinary_actions", ">=", 2]],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records",
        },
    },
    {
        "name": "Good candidate partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1],
        ],
        "action": {
            "decision": "AWARD PARTIAL",
            "reason": "Good academic & involvement record with moderate need",
        },
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000],
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score",
        },
    },
]


def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    """Evaluate a single condition tuple: [field, operator, value]."""
    if len(cond) != 3:
        return False
    field, op, value = cond
    if field not in facts or op not in OPS:
        return False
    try:
        return OPS[op](facts[field], value)
    except Exception:
        return False


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    """Check if all conditions in a rule evaluate to True (AND logic)."""
    return all(evaluate_condition(facts, c) for c in rule.get("conditions", []))


def run_rules(
    facts: Dict[str, Any], rules: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Returns (best_action, fired_rules)
    - best_action: highest priority rule among fired rules
    - fired_rules: list of matching rule dicts sorted by priority
    """
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return (
            {
                "decision": "REVIEW",
                "reason": "No matching rule conditions found for current facts",
            },
            [],
        )

    fired_sorted = sorted(
        fired, key=lambda r: r.get("priority", 0), reverse=True
    )
    best = fired_sorted[0].get(
        "action", {"decision": "REVIEW", "reason": "No action defined"}
    )
    return best, fired_sorted


# ----------------------------
# 2) Streamlit UI
# ----------------------------
st.set_page_config(
    page_title="Scholarship Advisory Rule-Based System",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 University Scholarship Advisory System")
st.caption("Knowledge Representation System (Rule-Based Engine) — BSD3513 Artificial Intelligence")

with st.sidebar:
    st.header("Applicant Facts Input")
    cgpa = st.number_input(
        "Cumulative GPA (CGPA)",
        min_value=0.00,
        max_value=4.00,
        step=0.01,
        value=3.75,
    )
    family_income = st.number_input(
        "Monthly Family Income (MYR)", min_value=0, step=500, value=5000
    )
    co_curricular_score = st.number_input(
        "Co-curricular Score (0-100)",
        min_value=0,
        max_value=100,
        step=1,
        value=85,
    )
    community_service_hours = st.number_input(
        "Community Service Hours", min_value=0, step=1, value=20
    )
    semester = st.number_input(
        "Current Semester", min_value=1, max_value=8, step=1, value=3
    )
    disciplinary_actions = st.number_input(
        "Disciplinary Actions Record", min_value=0, max_value=10, step=1, value=0
    )

    st.divider()
    st.header("Rules Configuration (JSON)")
    st.caption("Modify or extend active production rules below.")
    default_json = json.dumps(DEFAULT_RULES, indent=2)
    rules_text = st.text_area("JSON Rule Editor", value=default_json, height=350)

    run = st.button("Evaluate Application", type="primary")

facts = {
    "cgpa": float(cgpa),
    "family_income": float(family_income),
    "co_curricular_score": int(co_curricular_score),
    "community_service_hours": int(community_service_hours),
    "semester": int(semester),
    "disciplinary_actions": int(disciplinary_actions),
}

st.subheader("Submitted Applicant Profile")
st.json(facts)

try:
    rules = json.loads(rules_text)
    assert isinstance(rules, list), "Rules must be a valid JSON array"
except Exception as e:
    st.error(f"Invalid rules format in JSON Editor. Fallback to default rules. Details: {e}")
    rules = DEFAULT_RULES

st.divider()

if run:
    action, fired = run_rules(facts, rules)

    col1, col2 = st.columns([1, 1])
    with col1:
        st.subheader("System Recommendation")
        badge = action.get("decision", "REVIEW")
        reason = action.get("reason", "-")

        if badge == "AWARD FULL":
            st.success(f"🏆 **DECISION: {badge}**\n\n**Reason:** {reason}")
        elif badge == "AWARD PARTIAL":
            st.info(f"🥇 **DECISION: {badge}**\n\n**Reason:** {reason}")
        elif badge == "REJECT":
            st.error(f"❌ **DECISION: {badge}**\n\n**Reason:** {reason}")
        else:
            st.warning(f"⚠️ **DECISION: {badge}**\n\n**Reason:** {reason}")

    with col2:
        st.subheader("Matched Rules Audit Trail")
        if not fired:
            st.info("No matching rule conditions found.")
        else:
            for i, r in enumerate(fired, start=1):
                st.write(
                    f"**{i}. {r.get('name', '(unnamed)')}** | Priority: `{r.get('priority', 0)}`"
                )
                st.caption(f"Triggered Action: {r.get('action', {})}")
                with st.expander("Evaluated Conditions"):
                    for cond in r.get("conditions", []):
                        st.code(str(cond))
else:
    st.info("Adjust the applicant metrics in the sidebar and click **Evaluate Application**.")