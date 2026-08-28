from typing import Dict, List, Optional
from agents.shared.types import PracticalTask, TestCase, TaskType
from agents.shared.roles import RoleArchetype


# ── 1. Backend Software Engineer Task ──
backend_task = PracticalTask(
    task_id="backend_lru_cache",
    title="LRU Cache Implementation",
    description=(
        "Implement a Least Recently Used (LRU) Cache simulator with capacity constraint.\n"
        "Function: lru_cache_simulation(capacity: int, operations: List[List[Any]]) -> List[Any]\n"
        "Operations:\n"
        "  - ['put', key, value]: Inserts or updates key. If capacity exceeded, evicts LRU key. Returns None.\n"
        "  - ['get', key]: Returns the value of key if present, otherwise -1. Accessing moves key to most recently used."
    ),
    role_archetype=RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value,
    task_type=TaskType.CODING,
    language="python",
    function_name="lru_cache_simulation",
    starter_code="""def lru_cache_simulation(capacity: int, operations: list) -> list:
    # Write your solution here
    results = []
    return results
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_backend_1",
            input_params=[2, [["put", 1, 1], ["put", 2, 2], ["get", 1], ["put", 3, 3], ["get", 2], ["get", 3]]],
            expected_output=[None, None, 1, None, -1, 3],
            is_hidden=False,
            description="Basic LRU eviction with capacity 2"
        ),
        TestCase(
            test_case_id="tc_backend_2",
            input_params=[1, [["put", 5, 10], ["get", 5], ["put", 6, 20], ["get", 5], ["get", 6]]],
            expected_output=[None, 10, None, -1, 20],
            is_hidden=False,
            description="Capacity 1 eviction boundary"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_backend_hidden_1",
            input_params=[2, [["put", 1, 10], ["put", 1, 20], ["get", 1]]],
            expected_output=[None, None, 20],
            is_hidden=True,
            description="Update existing key value"
        ),
        TestCase(
            test_case_id="tc_backend_hidden_2",
            input_params=[3, [["put", 1, 1], ["put", 2, 2], ["put", 3, 3], ["get", 1], ["put", 4, 4], ["get", 2], ["get", 3], ["get", 4]]],
            expected_output=[None, None, None, 1, None, -1, 3, 4],
            is_hidden=True,
            description="Capacity 3 eviction order after read"
        ),
        TestCase(
            test_case_id="tc_backend_hidden_3",
            input_params=[2, [["get", 99], ["get", 100]]],
            expected_output=[-1, -1],
            is_hidden=True,
            description="Query non-existent keys in empty cache"
        )
    ],
    time_limit_minutes=15
)


# ── 2. Frontend Engineer Task ──
frontend_task = PracticalTask(
    task_id="frontend_flatten_object",
    title="Nested Object Flattener & Key Path Normalizer",
    description=(
        "Implement a JavaScript function flattenObject(obj) that converts deeply nested objects into a flat key-value map "
        "using dot-notation paths for nested keys. Ignore null/undefined values."
    ),
    role_archetype=RoleArchetype.FRONTEND_ENGINEER.value,
    task_type=TaskType.CODING,
    language="javascript",
    function_name="flattenObject",
    starter_code="""function flattenObject(obj) {
    // Write your solution here
    return {};
}
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_frontend_1",
            input_params=[{"user": {"name": "Alice", "address": {"city": "Paris"}}}],
            expected_output={"user.name": "Alice", "user.address.city": "Paris"},
            is_hidden=False,
            description="2-level nested object"
        ),
        TestCase(
            test_case_id="tc_frontend_2",
            input_params=[{"a": 1, "b": 2}],
            expected_output={"a": 1, "b": 2},
            is_hidden=False,
            description="Flat object"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_frontend_hidden_1",
            input_params=[{}],
            expected_output={},
            is_hidden=True,
            description="Empty object"
        ),
        TestCase(
            test_case_id="tc_frontend_hidden_2",
            input_params=[{"a": {"b": {"c": {"d": "deep"}}}}],
            expected_output={"a.b.c.d": "deep"},
            is_hidden=True,
            description="Deep 4-level nesting"
        ),
        TestCase(
            test_case_id="tc_frontend_hidden_3",
            input_params=[{"theme": {"colors": {"primary": "#3b82f6", "secondary": "#10b981"}}, "version": 1}],
            expected_output={"theme.colors.primary": "#3b82f6", "theme.colors.secondary": "#10b981", "version": 1},
            is_hidden=True,
            description="Design token hierarchy"
        )
    ],
    time_limit_minutes=15
)


# ── 3. Fullstack Engineer Task ──
fullstack_task = PracticalTask(
    task_id="fullstack_query_parser",
    title="REST API Query String Filter Parser",
    description=(
        "Implement parse_api_query(query_str: str) -> dict that parses URL query parameters into typed pagination and filter specs.\n"
        "Handles 'page' (int, default 1), 'limit' (int, default 10, max 100), 'sort' (str, default 'id'), and field filters (e.g. status=active)."
    ),
    role_archetype=RoleArchetype.FULLSTACK_ENGINEER.value,
    task_type=TaskType.CODING,
    language="python",
    function_name="parse_api_query",
    starter_code="""def parse_api_query(query_str: str) -> dict:
    # Write your solution here
    return {}
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_fullstack_1",
            input_params=["page=2&limit=25&sort=created_at&status=active"],
            expected_output={"page": 2, "limit": 25, "sort": "created_at", "filters": {"status": "active"}},
            is_hidden=False,
            description="Standard query with pagination and filters"
        ),
        TestCase(
            test_case_id="tc_fullstack_2",
            input_params=[""],
            expected_output={"page": 1, "limit": 10, "sort": "id", "filters": {}},
            is_hidden=False,
            description="Empty query with default values"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_fullstack_hidden_1",
            input_params=["limit=500&role=admin&verified=true"],
            expected_output={"page": 1, "limit": 100, "sort": "id", "filters": {"role": "admin", "verified": "true"}},
            is_hidden=True,
            description="Limit capping at 100 max"
        ),
        TestCase(
            test_case_id="tc_fullstack_hidden_2",
            input_params=["page=-5&limit=-10"],
            expected_output={"page": 1, "limit": 10, "sort": "id", "filters": {}},
            is_hidden=True,
            description="Invalid/negative page numbers normalized to default"
        )
    ],
    time_limit_minutes=15
)


# ── 4. Data Scientist / ML Engineer Task ──
data_ml_task = PracticalTask(
    task_id="data_ml_metrics",
    title="Binary Classification Metrics Calculator",
    description=(
        "Implement compute_classification_metrics(y_true: List[int], y_pred: List[int]) -> dict.\n"
        "Returns precision, recall, and f1 rounded to 4 decimal places. Returns 0.0 if denominator is 0."
    ),
    role_archetype=RoleArchetype.DATA_SCIENTIST_ML.value,
    task_type=TaskType.CODING,
    language="python",
    function_name="compute_classification_metrics",
    starter_code="""def compute_classification_metrics(y_true: list, y_pred: list) -> dict:
    # Write your solution here
    return {"precision": 0.0, "recall": 0.0, "f1": 0.0}
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_data_1",
            input_params=[[1, 1, 0, 0, 1], [1, 0, 0, 1, 1]],
            expected_output={"precision": 0.6667, "recall": 0.6667, "f1": 0.6667},
            is_hidden=False,
            description="Standard binary predictions (TP=2, FP=1, FN=1, TN=1)"
        ),
        TestCase(
            test_case_id="tc_data_2",
            input_params=[[1, 1, 1], [1, 1, 1]],
            expected_output={"precision": 1.0, "recall": 1.0, "f1": 1.0},
            is_hidden=False,
            description="Perfect classification"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_data_hidden_1",
            input_params=[[1, 1, 1], [0, 0, 0]],
            expected_output={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            is_hidden=True,
            description="Zero true positives"
        ),
        TestCase(
            test_case_id="tc_data_hidden_2",
            input_params=[[0, 0, 0], [1, 1, 1]],
            expected_output={"precision": 0.0, "recall": 0.0, "f1": 0.0},
            is_hidden=True,
            description="All false alarms"
        )
    ],
    time_limit_minutes=15
)


# ── 5. DevOps & Cloud Engineer Task ──
devops_task = PracticalTask(
    task_id="devops_log_parser",
    title="Log Stream Anomaly Spike Detector",
    description=(
        "Implement detect_error_spikes(log_entries: List[str], error_threshold: int) -> List[str].\n"
        "Log format: 'YYYY-MM-DD HH:MM:SS [LEVEL] [SERVICE] Message'.\n"
        "Returns list of SERVICE names whose ERROR count >= error_threshold, sorted alphabetically."
    ),
    role_archetype=RoleArchetype.DEVOPS_CLOUD.value,
    task_type=TaskType.CODING,
    language="python",
    function_name="detect_error_spikes",
    starter_code="""def detect_error_spikes(log_entries: list, error_threshold: int) -> list:
    # Write your solution here
    return []
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_devops_1",
            input_params=[
                [
                    "2026-08-26 10:00:01 [ERROR] [auth-service] DB Connection timeout",
                    "2026-08-26 10:00:02 [INFO] [api-gateway] Request routed",
                    "2026-08-26 10:00:03 [ERROR] [auth-service] Redis read failure",
                    "2026-08-26 10:00:04 [ERROR] [payment-service] Gateway 504"
                ],
                2
            ],
            expected_output=["auth-service"],
            is_hidden=False,
            description="Threshold 2 matches auth-service"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_devops_hidden_1",
            input_params=[
                [
                    "2026-08-26 10:00:01 [WARN] [worker] High memory",
                    "2026-08-26 10:00:02 [INFO] [worker] Cleaned up"
                ],
                1
            ],
            expected_output=[],
            is_hidden=True,
            description="No ERROR levels present"
        ),
        TestCase(
            test_case_id="tc_devops_hidden_2",
            input_params=[
                [
                    "2026-08-26 10:00:01 [ERROR] [svc-b] Fatal crash",
                    "2026-08-26 10:00:02 [ERROR] [svc-a] Fatal crash",
                    "2026-08-26 10:00:03 [ERROR] [svc-b] Restart failed",
                    "2026-08-26 10:00:04 [ERROR] [svc-a] Disk full"
                ],
                2
            ],
            expected_output=["svc-a", "svc-b"],
            is_hidden=True,
            description="Multiple services meeting threshold, sorted alphabetically"
        )
    ],
    time_limit_minutes=15
)


# ── 6. Cybersecurity & AppSec Task ──
security_task = PracticalTask(
    task_id="security_sanitizer",
    title="Security Threat & Injection Payload Detector",
    description=(
        "Implement detect_security_threats(payloads: List[str]) -> dict.\n"
        "Counts occurrences of: 'sqli' (patterns: union select, or 1=1, --, /*), 'xss' (patterns: <script, javascript:, onerror=), and 'benign'.\n"
        "Returns {'sqli': count, 'xss': count, 'benign': count}."
    ),
    role_archetype=RoleArchetype.CYBERSECURITY.value,
    task_type=TaskType.CODING,
    language="python",
    function_name="detect_security_threats",
    starter_code="""def detect_security_threats(payloads: list) -> dict:
    # Write your solution here
    return {"sqli": 0, "xss": 0, "benign": 0}
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_sec_1",
            input_params=[[
                "SELECT * FROM users WHERE id = 1 OR 1=1 --",
                "<script>alert('XSS')</script>",
                "john_doe@example.com"
            ]],
            expected_output={"sqli": 1, "xss": 1, "benign": 1},
            is_hidden=False,
            description="1 SQLi, 1 XSS, 1 Benign"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_sec_hidden_1",
            input_params=[[
                "admin' UNION SELECT null, username, password FROM users/*",
                "<img src=x onerror=alert(1)>",
                "normal query text"
            ]],
            expected_output={"sqli": 1, "xss": 1, "benign": 1},
            is_hidden=True,
            description="Advanced SQLi union and onerror XSS"
        ),
        TestCase(
            test_case_id="tc_sec_hidden_2",
            input_params=[[]],
            expected_output={"sqli": 0, "xss": 0, "benign": 0},
            is_hidden=True,
            description="Empty payload list"
        )
    ],
    time_limit_minutes=15
)


# ── 7. Mobile Application Engineer Task ──
mobile_task = PracticalTask(
    task_id="mobile_cache_resolver",
    title="Offline Sync & Conflict Resolver",
    description=(
        "Implement resolveSyncConflicts(serverItems, clientItems) in JavaScript.\n"
        "Items have shape: { id: string, version: number, updatedAt: number, data: string, isDeleted: boolean }.\n"
        "Resolves conflict per id: Item with higher updatedAt wins. If identical, higher version wins. Returns merged array sorted by id."
    ),
    role_archetype=RoleArchetype.MOBILE_ENGINEER.value,
    task_type=TaskType.CODING,
    language="javascript",
    function_name="resolveSyncConflicts",
    starter_code="""function resolveSyncConflicts(serverItems, clientItems) {
    // Write your solution here
    return [];
}
""",
    visible_test_cases=[
        TestCase(
            test_case_id="tc_mobile_1",
            input_params=[
                [{"id": "doc_1", "version": 1, "updatedAt": 100, "data": "Server draft", "isDeleted": False}],
                [{"id": "doc_1", "version": 2, "updatedAt": 200, "data": "Offline edit", "isDeleted": False}]
            ],
            expected_output=[{"id": "doc_1", "version": 2, "updatedAt": 200, "data": "Offline edit", "isDeleted": False}],
            is_hidden=False,
            description="Client edit with newer timestamp wins"
        )
    ],
    hidden_test_cases=[
        TestCase(
            test_case_id="tc_mobile_hidden_1",
            input_params=[
                [{"id": "doc_a", "version": 2, "updatedAt": 300, "data": "Server", "isDeleted": False}],
                [{"id": "doc_b", "version": 1, "updatedAt": 100, "data": "Client Only", "isDeleted": False}]
            ],
            expected_output=[
                {"id": "doc_a", "version": 2, "updatedAt": 300, "data": "Server", "isDeleted": False},
                {"id": "doc_b", "version": 1, "updatedAt": 100, "data": "Client Only", "isDeleted": False}
            ],
            is_hidden=True,
            description="Disjoint items merged and sorted"
        )
    ],
    time_limit_minutes=15
)


# ── 8. UI/UX Designer Practical Case ──
uiux_task = PracticalTask(
    task_id="uiux_design_case",
    title="Design System & WCAG 2.1 Accessibility Critique",
    description=(
        "Evaluate a mobile checkout redesign proposal against WCAG 2.1 AA accessibility guidelines.\n"
        "Provide specific structural critiques on:\n"
        "1. Touch target sizes and tap area padding.\n"
        "2. Color contrast ratios for text and primary CTA buttons.\n"
        "3. Error state announcements and screen reader affordances.\n"
        "4. Progressive disclosure vs cognitive load."
    ),
    role_archetype=RoleArchetype.UI_UX_DESIGNER.value,
    task_type=TaskType.UX_DESIGN_CASE,
    language="markdown",
    instructions="Write a structured design review covering accessibility, component reusability, and user journey optimization.",
    rubric={
        "accessibility": "Identification of WCAG 2.1 AA contrast and touch target violations",
        "hierarchy": "Visual hierarchy and reduction of cognitive load",
        "design_system": "Use of standardized design tokens and reusable components"
    },
    time_limit_minutes=15
)


# ── 9. Technical Product Manager Practical Case ──
pm_task = PracticalTask(
    task_id="pm_prd_case",
    title="0-to-1 MVP Feature Prioritization & North Star Metric Design",
    description=(
        "Given a SaaS collaboration tool expanding into AI-assisted note taking:\n"
        "1. Formulate the core North Star Metric and 2 guardrail metrics.\n"
        "2. Prioritize 4 candidate features using the RICE framework (Reach, Impact, Confidence, Effort).\n"
        "3. Specify MVP launch criteria and a rollback/contingency plan."
    ),
    role_archetype=RoleArchetype.PRODUCT_MANAGER.value,
    task_type=TaskType.PRD_CASE,
    language="markdown",
    instructions="Provide a structured PRD snippet with metric definitions, RICE scoring matrix, and launch risk trade-offs.",
    rubric={
        "metric_clarity": "Precise North Star Metric and guardrails",
        "prioritization": "Rigorous RICE framework calculations",
        "execution": "Realistic MVP scope and launch criteria"
    },
    time_limit_minutes=15
)


PRACTICAL_TASKS: Dict[str, PracticalTask] = {
    RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value: backend_task,
    RoleArchetype.FRONTEND_ENGINEER.value: frontend_task,
    RoleArchetype.FULLSTACK_ENGINEER.value: fullstack_task,
    RoleArchetype.DATA_SCIENTIST_ML.value: data_ml_task,
    RoleArchetype.DEVOPS_CLOUD.value: devops_task,
    RoleArchetype.CYBERSECURITY.value: security_task,
    RoleArchetype.MOBILE_ENGINEER.value: mobile_task,
    RoleArchetype.UI_UX_DESIGNER.value: uiux_task,
    RoleArchetype.PRODUCT_MANAGER.value: pm_task,
}


def get_practical_task_for_role(role_archetype: str) -> PracticalTask:
    """Retrieve the designated practical assessment task for a given role archetype."""
    role_clean = str(role_archetype).upper().replace(" ", "_").replace("/", "_").replace("-", "_")
    return PRACTICAL_TASKS.get(role_clean, PRACTICAL_TASKS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND.value])

