from enum import Enum
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field


class RoleArchetype(str, Enum):
    SOFTWARE_ENGINEER_BACKEND = "SOFTWARE_ENGINEER_BACKEND"
    FRONTEND_ENGINEER = "FRONTEND_ENGINEER"
    FULLSTACK_ENGINEER = "FULLSTACK_ENGINEER"
    DATA_SCIENTIST_ML = "DATA_SCIENTIST_ML"
    DEVOPS_CLOUD = "DEVOPS_CLOUD"
    CYBERSECURITY = "CYBERSECURITY"
    MOBILE_ENGINEER = "MOBILE_ENGINEER"
    UI_UX_DESIGNER = "UI_UX_DESIGNER"
    PRODUCT_MANAGER = "PRODUCT_MANAGER"


class RoleBlueprint(BaseModel):
    role: RoleArchetype
    display_name: str
    required_competencies: List[str] = Field(default_factory=list)
    topic_trees: Dict[str, List[str]] = Field(default_factory=dict)
    technical_topics: List[str] = Field(default_factory=list)
    project_topics: List[str] = Field(default_factory=list)
    behavioral_topics: List[str] = Field(default_factory=list)
    hr_topics: List[str] = Field(default_factory=list)
    stage_weighting: Dict[str, float] = Field(default_factory=dict)
    recommended_practical_assessment: str = "System and API Architecture"
    keywords: List[str] = Field(default_factory=list)
    minimum_technical_evidence: int = 4
    minimum_project_evidence: int = 2
    minimum_behavioral_evidence: int = 2
    minimum_hr_evidence: int = 1


role_backend = RoleBlueprint(
    role=RoleArchetype.SOFTWARE_ENGINEER_BACKEND,
    display_name="Backend Software Engineer",
    required_competencies=[
        "Data Structures and Algorithms",
        "API Design and Microservices",
        "Database Design and Scaling",
        "Concurrency and Performance",
        "Caching and Messaging Systems"
    ],
    topic_trees={
        "Fundamentals": ["Memory Management", "Concurrency", "OOP/FP Principles", "Data Structures"],
        "System Design": ["Database Sharding", "Caching Strategies", "Message Brokers", "Load Balancing"],
        "API & Architecture": ["REST/gRPC/GraphQL", "Microservices Communication", "Distributed Transactions"],
    },
    technical_topics=[
        "Data Structures and Algorithms",
        "API Design and REST/gRPC Protocols",
        "Database Indexing and Query Optimization",
        "Concurrency and Multithreading",
        "Caching Strategies (Redis/Memcached)"
    ],
    project_topics=[
        "Distributed System Architecture and Microservices",
        "Database Sharding and Read Replication",
        "Asynchronous Message Queues and Event-Driven Systems",
        "High-Throughput API Gateway and Rate Limiting"
    ],
    behavioral_topics=[
        "Engineering Disagreements and Code Review Conflicts",
        "Production Outage Postmortem and Triage Under Pressure",
        "Cross-Team Technical Leadership"
    ],
    hr_topics=[
        "Engineering Culture and Continuous Technical Growth",
        "Career Goals and Engineering Philosophy"
    ],
    stage_weighting={
        "technical": 0.35,
        "practical": 0.20,
        "problem_solving": 0.20,
        "communication": 0.10,
        "behavioral": 0.10,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Algorithm and Backend API Design",
    keywords=["backend", "python", "java", "golang", "c++", "fastapi", "django", "spring", "microservices", "sql", "postgresql", "redis", "kafka"]
)


role_frontend = RoleBlueprint(
    role=RoleArchetype.FRONTEND_ENGINEER,
    display_name="Frontend Engineer",
    required_competencies=[
        "JavaScript/TypeScript and Modern Frameworks",
        "DOM, Virtual DOM and State Management",
        "CSS Architecture, Responsive Design and Layouts",
        "Web Performance and Core Web Vitals",
        "Browser Security and Accessibility (a11y)"
    ],
    topic_trees={
        "Core Frontend": ["JavaScript Event Loop", "TypeScript Generics", "DOM Manipulation", "CSS Grid and Flexbox"],
        "Framework & State": ["React Reconciliation", "State Management (Redux/zustand)", "Hooks and Lifecycle", "Server Components"],
        "Performance & Web": ["Bundle Optimization", "Lazy Loading and Code Splitting", "Core Web Vitals", "SSR vs CSR"],
    },
    technical_topics=[
        "JavaScript Event Loop and Async Execution",
        "TypeScript Advanced Types and Generics",
        "DOM and Virtual DOM Reconciliation (React/Next.js)",
        "CSS Grid, Flexbox and Responsive Layouts",
        "Browser Rendering Pipeline and Core Web Vitals"
    ],
    project_topics=[
        "Component-Driven Frontend Architecture",
        "Global State Management and Client Caching",
        "Bundle Optimization and Code Splitting",
        "Web Accessibility (WCAG) and Design System Implementation"
    ],
    behavioral_topics=[
        "Design vs Engineering Trade-offs and Alignment",
        "Debugging Complex Production UI Incidents",
        "Mentoring and Establishing Frontend Best Practices"
    ],
    hr_topics=[
        "Frontend Engineering Culture and Modern Web Evolution",
        "Career Goals and Growth Trajectory"
    ],
    stage_weighting={
        "technical": 0.30,
        "practical": 0.25,
        "problem_solving": 0.20,
        "communication": 0.10,
        "behavioral": 0.10,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Component Architecture and Frontend Debugging",
    keywords=["frontend", "react", "next.js", "vue", "angular", "typescript", "javascript", "css", "html", "tailwind", "redux", "web vitals", "ui"]
)

role_fullstack = RoleBlueprint(
    role=RoleArchetype.FULLSTACK_ENGINEER,
    display_name="Full Stack Engineer",
    required_competencies=[
        "End-to-End Application Architecture",
        "Frontend Frameworks and UI State",
        "Backend APIs and Database Optimization",
        "Authentication and Security",
        "CI/CD and Cloud Deployment"
    ],
    topic_trees={
        "Frontend Layer": ["React/Vue UI Development", "Client State", "Responsive UI"],
        "Backend Layer": ["REST/GraphQL APIs", "Database Optimization", "Auth & JWT"],
        "Integration & DevOps": ["Full-Stack Deployment", "Docker Containers", "End-to-End Testing"],
    },
    technical_topics=[
        "Full-Stack State Management and  API Contract Design",
        "Database Query Performance and ORMs",
        "Authentication Flows (OAuth/JWT/Sessions)",
        "Server-Side Rendering vs Client-Side Rendering"
    ],
    project_topics=[
        "End-to-End Feature Architecture and Data Flow",
        "Full-Stack Deployment and Containierization",
        "Real-Time WebSocket and Push Architecture",
        "API Security and Cross-Origin Resource Sharing"
    ],
    behavioral_topics=[
        "Balancing Frontend and Backend Technical Debt",
        "Cross-Functional Collaboration with Product and Design",
        "Delivering Under Aggressive Timelines"
    ],
    hr_topics=[
        "Full-Stack Versatility and Team Culture",
        "Career Milestones and Engineering Impact"
    ],
    stage_weighting={
        "technical": 0.30,
        "practical": 0.25,
        "problem_solving": 0.20,
        "communication": 0.10,
        "behavioral": 0.10,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Full-Stack Feature Implementation",
    keywords=["fullstack", "full stack", "node.js", "express", "react", "mern", "django", "postgresql", "full-stack"]
)

role_data_ml = RoleBlueprint(
    role=RoleArchetype.DATA_SCIENTIST_ML,
    display_name="Data Scientist / ML Engineer",
    required_competencies=[
        "Machine Learning Algorithms and Deep Learning",
        "Feature Engineering and Data Preprocessing",
        "Model Evaluation, Validation and Metrics",
        "MLOps, Model Serving and Pipelines",
        "Statistics and Probability"
    ],
    topic_trees={
        "Modeling": ["Supervised and Unsupervised Learning", "Neural Networks", "Transformer Architectures", "Loss Functions"],
        "Data Pipeline": ["Feature Engineering", "Data Cleaning", "Pandas/NumPy", "SQL Aggregations"],
        "MLOps & Deployment": ["Model Drift and Monitoring", "ONNX/TorchScript", "FastAPI Model Serving", "Vector Databases and Embeddings"],
    },
    technical_topics=[
        "Supervised vs Unsupervised Algorithms and Mathematical Foundations",
        "Feature Engineering and Dimensionality Reduction",
        "Model Evaluation Metrics (ROC-AUC, Precision-Recall, F1)",
        "Loss Functions and Optimization (Gradient Descent/Adam)",
        "Deep Learning and Transformer Architectures"
    ],
    project_topics=[
        "End-to-End ML Pipeline Architecture",
        "Model Drift Detection and Continuous Retraining",
        "Low-Latency Model Serving (TorchScript/Triton/FastAPI)",
        "Vector Databases and Embedding Search Systems"
    ],
    behavioral_topics=[
        "Communicating Complex ML Insights to Non-Technical Stakeholders",
        "Handling Data Quality Issues and Model Biases",
        "Prioritizing Experiments vs Production Delivery"
    ],
    hr_topics=[
        "AI/ML Research Culture and Responsible AI",
        "Long-Term ML Career Goals"
    ],
    stage_weighting={
        "technical": 0.35,
        "practical": 0.20,
        "problem_solving": 0.25,
        "communication": 0.10,
        "behavioral": 0.05,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Data Pipeline and Model Metric Optimization",
    keywords=["data science", "machine learning", "ml", "ai", "deep learning", "pytorch", "tensorflow", "scikit-learn", "nlp", "computer vision", "llm", "pandas", "data engineer"]
)


role_devops = RoleBlueprint(
    role=RoleArchetype.DEVOPS_CLOUD,
    display_name="DevOps & Cloud Platform Engineer",
    required_competencies=[
        "Containerization and Orchestration (Docker, Kubernetes)",
        "Infrastructure as Code (Terraform, CloudFormation)",
        "CI/CD Pipelines and Automation",
        "Observability, Monitoring and Log Aggregation",
        "Cloud Security and High Availability"
    ],
    topic_trees={
        "Containers & Cloud": ["Docker Layer Caching", "Kubernetes Pod Lifecycle and Ingress", "AWS/GCP/Azure Services"],
        "Infrastructure as Code": ["Terraform State and Modules", "Ansible Automation", "GitOps (ArgoCD)"],
        "Operations & Reliability": ["Prometheus/Grafana Alerting", "Incident Triage", "Disaster Recovery and Multi-AZ"],
    },
    technical_topics=[
        "Linux Kernel, Networking and Process Isolation",
        "Containerization and Docker Layer Optimization",
        "Kubernetes Pod Lifecycle, Ingress and Services",
        "Infrastructure as Code with Terraform",
        "CI/CD Pipeline Security and Automation"
    ],
    project_topics=[
        "Multi-AZ High Availability and Disaster Recovery Architecture",
        "Centralized Observability (Prometheus, Grafana, OpenTelemetry)",
        "Zero-Downtime Deployment Strategies (Canary/Blue-Green)",
        "Cloud Security, IAM and Secrets Management"
    ],
    behavioral_topics=[
        "Major Production Incident Command and Post-Incident Learning",
        "Bridging Developer Velocity and Infrastructure Reliability",
        "Advocating for Reliability and Technical Debt Remediation"
    ],
    hr_topics=[
        "SRE Culture, Blameless Postmortems and Growth",
        "DevOps Philosophy and Career Path"
    ],
    stage_weighting={
        "technical": 0.35,
        "practical": 0.25,
        "problem_solving": 0.20,
        "communication": 0.10,
        "behavioral": 0.05,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Infrastructure-as-Code and Incident Triage",
    keywords=["devops", "cloud", "aws", "gcp", "azure", "kubernetes", "k8s", "docker", "terraform", "ci/cd", "jenkins", "github actions", "prometheus", "grafana", "sre", "linux"]
)


role_security = RoleBlueprint(
    role=RoleArchetype.CYBERSECURITY,
    display_name="Cybersecurity & AppSec Engineer",
    required_competencies=[
        "Application Security and OWASP Top 10",
        "Authentication, Authorization (OAuth, OIDC, SAML)",
        "Cryptography and Secure Communication",
        "Threat Modeling and Vulnerability Assessment",
        "Network Security and Incident Response"
    ],
    topic_trees={
        "AppSec": ["OWASP Vulnerabilities (SQLi, XSS, CSRF, SSRF)", "Secure Code Review", "Secrets Management"],
        "Auth & Crypto": ["OAuth2 / OIDC Flows", "Public-Key Cryptography (PKI)", "mTLS and JWT Security"],
        "Defense & Operations": ["Threat Modeling (STRIDE)", "SIEM and Intrusion Detection", "Zero Trust Architecture"],
    },
    technical_topics=[
        "OWASP Top 10 Vulnerabilities and Remediation",
        "Authentication Protocols (OAuth2, OIDC, SAML, mTLS)",
        "Symmetric vs Asymmetric Cryptography and PKI",
        "Network Protocols and Packet Analysis",
        "Secure Code Review and Static Analysis (SAST/DAST)"
    ],
    project_topics=[
        "Zero Trust Security Architecture and Network Segmentation",
        "Threat Modeling (STRIDE) for Cloud Applications",
        "Security Information and Event Management (SIEM) Alerting",
        "Incident Response and Breach Containment Strategy"
    ],
    behavioral_topics=[
        "Enforcing Security Standards Without Hindering Developer Velocity",
        "Handling a Critical Zero-Day Vulnerability Disclosure",
        "Executive Communication During Security Incidents"
    ],
    hr_topics=[
        "Security Ethics, Continuous Defense Learning",
        "AppSec Career Goals"
    ],
    stage_weighting={
        "technical": 0.35,
        "practical": 0.25,
        "problem_solving": 0.20,
        "communication": 0.10,
        "behavioral": 0.05,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Vulnerability Triage and Security Architecture",
    keywords=["security", "cybersecurity", "appsec", "infosec", "penetration testing", "owasp", "oauth", "cryptography", "soc", "siem", "zero trust"]
)


role_mobile = RoleBlueprint(
    role=RoleArchetype.MOBILE_ENGINEER,
    display_name="Mobile Application Engineer",
    required_competencies=[
        "Mobile Platform Architectures (iOS/Android/Flutter/React Native)",
        "App Lifecycle, Memory Management and Performance",
        "Offline Storage, Sync and State Management",
        "Native APIs and Device Hardware Integration",
        "App Store Guidelines and Security"
    ],
    topic_trees={
        "Core Mobile": ["App Lifecycle Events", "Memory Management and Leaks", "UI Threading and Background Tasks"],
        "Data & Networking": ["Offline Cache and SQLite/CoreData", "REST/GraphQL Mobile Integration", "Push Notifications"],
        "Platform & Release": ["App Store / Play Store Build Pipelines", "Deep Linking", "Biometric Auth and Security"],
    },
    technical_topics=[
        "Mobile Application Lifecycle and Background State Handling",
        "Memory Management, Leaks and Profiling",
        "UI Threading, Coroutines and Reactive Streams",
        "Offline SQLite/CoreData Storage and Conflict Sync",
        "Native Bridge and Platform Channel Communication"
    ],
    project_topics=[
        "Modular Mobile Application Architecture",
        "Secure Biometric Authentication and KeyStore/KeyChain",
        "Deep Linking and Push Notification Architecture",
        "App Store Build Pipelines and Over-The-Air Updates"
    ],
    behavioral_topics=[
        "Managing Device Fragmentation and OS Version Support",
        "Coordinating Complex Releases with Backend API Teams",
        "Triage of Critical Mobile Crash Regressions"
    ],
    hr_topics=[
        "Mobile Craftsmanship and UX Excellence",
        "Engineering Goals and Platform Specialization"
    ],
    stage_weighting={
        "technical": 0.30,
        "practical": 0.25,
        "problem_solving": 0.20,
        "communication": 0.10,
        "behavioral": 0.10,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Mobile Architecture and Lifecycle Problem",
    keywords=["mobile", "android", "ios", "swift", "kotlin", "react native", "flutter", "mobile app", "xcode"]
)


role_uiux = RoleBlueprint(
    role=RoleArchetype.UI_UX_DESIGNER,
    display_name="UI/UX Designer",
    required_competencies=[
        "User Research and Usability Testing",
        "Information Architecture and User Journeys",
        "Design Systems and Component Libraries",
        "Wireframing and High-Fidelity Prototyping",
        "Accessibility (WCAG) and Responsive Design"
    ],
    topic_trees={
        "Design Fundamentals": ["Typography and Color Theory", "Visual Hierarchy", "Design Systems (Figma)"],
        "User Experience": ["User Journey Mapping", "Wireframing and Prototyping", "Usability Testing and Feedback Loops"],
        "Accessibility & Handoff": ["WCAG 2.1 Accessibility", "Developer Handoff Specs", "Interaction Micro-animations"],
    },
    technical_topics=[
        "User Research Methodologies and Qualitative/Quantitative Synthesis",
        "Information Architecture and User Flow Mapping",
        "Design System Governance and Tokenization in Figma",
        "WCAG 2.1 AA Accessibility Standards",
        "Interaction Design and Micro-animations"
    ],
    project_topics=[
        "End-to-End Product Design Case Walkthrough",
        "Usability Testing Protocols and Iterative Prototyping",
        "Responsive Web and Mobile Design Adaptation",
        "Developer Handoff Specifications and Component Consistency"
    ],
    behavioral_topics=[
        "Navigating Stakeholder Pushback and Conflicting Requirements",
        "Aligning User Advocacy with Business Constraints",
        "Presenting Design Rationale with Data"
    ],
    hr_topics=[
        "Design Culture, Empathy and Collaborative Process",
        "Product Design Aspirations and Impact"
    ],
    stage_weighting={
        "technical": 0.20,
        "practical": 0.30,
        "problem_solving": 0.20,
        "communication": 0.15,
        "behavioral": 0.10,
        "role_fit": 0.05
    },
    recommended_practical_assessment="UX Wireframing and Usability Critique",
    keywords=["ui", "ux", "ui/ux", "designer", "product design", "figma", "wireframe", "prototype", "user research", "usability", "design system"]
)


role_pm = RoleBlueprint(
    role=RoleArchetype.PRODUCT_MANAGER,
    display_name="Technical Product Manager",
    required_competencies=[
        "Product Strategy and Roadmap Prioritization",
        "Product Metrics, OKRs and Data-Driven Decisions",
        "User Persona Definition and Problem Discovery",
        "Stakeholder Management and Cross-Functional Alignment",
        "Technical Feasibility and System Trade-offs"
    ],
    topic_trees={
        "Product Sense": ["User Problem Discovery", "Feature Prioritization (RICE/MoSCoW)", "Product Metrics (AARRR/North Star)"],
        "Execution & Delivery": ["Sprint Planning and Agile", "MVP Definition", "Release Strategy and Launch Risk"],
        "Leadership & Strategy": ["Stakeholder Conflict Resolution", "Market and Competitive Analysis", "Data-Driven Iteration"],
    },
    technical_topics=[
        "User Problem Discovery and Customer Interview Frameworks",
        "Product Metrics (North Star, AARRR, Retention Cohorts)",
        "Feature Prioritization Frameworks (RICE, MoSCoW, Kano)",
        "Technical Feasibility Assessment and System Trade-offs",
        "Product Requirements Document (PRD) Crafting"
    ],
    project_topics=[
        "End-to-End 0-to-1 MVP Definition and Launch Strategy",
        "A/B Testing Hypothesis Design and Statistical Significance",
        "Market and Competitive Landscape Positioning",
        "Sprint Planning and Agile Delivery Execution"
    ],
    behavioral_topics=[
        "Cross-Functional Conflict Resolution (Eng vs Design vs Execs)",
        "Managing Unrealistic Timelines and Scope Negotiation",
        "Handling a Product Launch Failure with Data-Driven Pivots"
    ],
    hr_topics=[
        "Product Vision, Customer Obsession and Culture",
        "Leadership Trajectory and PM Philosophy"
    ],
    stage_weighting={
        "technical": 0.15,
        "practical": 0.20,
        "problem_solving": 0.25,
        "communication": 0.20,
        "behavioral": 0.15,
        "role_fit": 0.05
    },
    recommended_practical_assessment="Product PRD and Feature Prioritization Case",
    keywords=["product manager", "pm", "product management", "scrum", "agile", "roadmap", "prds", "user stories", "kpis", "okrs", "metrics"]
)


ROLE_BLUEPRINTS: Dict[RoleArchetype, RoleBlueprint] = {
    RoleArchetype.SOFTWARE_ENGINEER_BACKEND: role_backend,
    RoleArchetype.FRONTEND_ENGINEER: role_frontend,
    RoleArchetype.FULLSTACK_ENGINEER: role_fullstack,
    RoleArchetype.DATA_SCIENTIST_ML: role_data_ml,
    RoleArchetype.DEVOPS_CLOUD: role_devops,
    RoleArchetype.CYBERSECURITY: role_security,
    RoleArchetype.MOBILE_ENGINEER: role_mobile,
    RoleArchetype.UI_UX_DESIGNER: role_uiux,
    RoleArchetype.PRODUCT_MANAGER: role_pm,
}


def get_role_blueprint(role: Union[RoleArchetype, str]) -> RoleBlueprint:
    """Retrieve the blueprint for a given role archetype or string alias."""
    if isinstance(role, RoleArchetype):
        return ROLE_BLUEPRINTS.get(role, ROLE_BLUEPRINTS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND])
    
    role_str = str(role).upper().replace(" ", "_").replace("/", "_").replace("-", "_")
    for r1, bp in ROLE_BLUEPRINTS.items():
        if r1.value == role_str or r1.name == role_str:
            return bp
            
    low_str = str(role).lower()
    for r1, bp in ROLE_BLUEPRINTS.items():
        if any(kw in low_str for kw in bp.keywords):
            return bp
            
    return ROLE_BLUEPRINTS[RoleArchetype.SOFTWARE_ENGINEER_BACKEND]


def detect_role(
    target_role_str: Optional[str] = None,
    jd_text: Optional[str] = None,
    profile_skills: Optional[List[str]] = None,
    profile_experience: Optional[List[str]] = None
) -> RoleArchetype:
    """Determine the optimal RoleArchetype using explicit target role, JD text, or profile evidence.
    
    Priority:
    1. Explicit target role string if provided
    2. Target Job Description text
    3. Candidate profile skills and experience
    4. Fallback: SOFTWARE_ENGINEER_BACKEND
    """
    if target_role_str and target_role_str.strip():
        bp = get_role_blueprint(target_role_str.strip())
        return bp.role

    def _score_text(text: str) -> Dict[RoleArchetype, int]:
        scores = {r1: 0 for r1 in RoleArchetype}
        low = text.lower()
        for r1, bp1 in ROLE_BLUEPRINTS.items():
            for kw in bp1.keywords:
                if kw in low:
                    scores[r1] += 2 if f" {kw} " in f" {low} " else 1
        return scores

    if jd_text and jd_text.strip():
        jd_scores = _score_text(jd_text)
        best_role, best_score = max(jd_scores.items(), key=lambda item: item[1])
        if best_score > 0:
            return best_role

    candidate_corpus = " ".join((profile_skills or []) + (profile_experience or []))
    if candidate_corpus.strip():
        cand_scores = _score_text(candidate_corpus)
        best_role, best_score = max(cand_scores.items(), key=lambda item: item[1])
        if best_score > 0:
            return best_role

    return RoleArchetype.SOFTWARE_ENGINEER_BACKEND
