// PrepSense API Client
const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api';

export interface ResumeData {
  success: boolean;
  candidate_name: string;
  candidate_email: string;
  skills: string[];
  experience_years: number;
  detected_role: string;
  raw_summary: string;
}

export interface JDMatchResult {
  matched_role: string;
  match_score: number;
  matched_competencies: string[];
  missing_competencies: string[];
  role_blueprint_summary: string;
}

export interface SessionInit {
  session_id: string;
  candidate_name: string;
  target_role: string;
  total_stages: number;
  stage_order: string[];
}

export interface QuestionData {
  question_id: string;
  question_text: string;
  stage: string;
  topic: string;
  difficulty: string;
  question_index: number;
  total_estimated: number;
  is_followup: boolean;
}

export interface SubmitAnswerResult {
  session_id: string;
  answer_acknowledged: boolean;
  next_question: QuestionData | null;
  current_stage: string;
  is_practical_ready: boolean;
  is_completed: boolean;
  total_questions_asked: number;
}

export interface TestCase {
  test_case_id: string;
  input_params: any;
  expected_output: any;
  description: string;
}

export interface PracticalTask {
  task_id: string;
  title: string;
  description: string;
  role_archetype: string;
  task_type: string;
  language: string;
  starter_code: string;
  instructions: string;
  visible_test_cases: TestCase[];
  hidden_test_count: number;
  time_limit_minutes: number;
}

export interface ExecutionResultItem {
  test_case_id: string;
  passed: boolean;
  actual_output?: any;
  expected_output?: any;
  execution_time_ms: number;
  error_message?: string;
}

export interface PracticalSubmitResult {
  task_id: string;
  task_title: string;
  role_archetype: string;
  language: string;
  tests_passed: number;
  total_tests: number;
  hidden_tests_passed: number;
  total_hidden_tests: number;
  correctness_score: number;
  edge_case_score: number;
  complexity_score: number;
  code_quality_score: number;
  overall_practical_score: number;
  time_complexity: string;
  space_complexity: string;
  feedback: string;
  execution_results: ExecutionResultItem[];
}

export interface FinalReport {
  session_id: string;
  candidate_name: string;
  target_role: string;
  overall_summary: string;
  technical_assessment: string;
  communication_assessment: string;
  hiring_recommendation: string;
  confidence_level: string;
  final_score: number;
  dimension_scores: {
    technical: number;
    practical: number;
    problem_solving: number;
    communication: number;
    behavioral: number;
    role_fit: number;
    confidence: number;
    overall: number;
  };
  strengths: string[];
  weaknesses: string[];
  improvement_plan: string[];
  practical_evaluation?: any;
}

// Helper to add auth header
const getHeaders = (extraHeaders: Record<string, string> = {}) => {
  const token = typeof window !== 'undefined' ? localStorage.getItem('prepsense_token') : null;
  return {
    ...extraHeaders,
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

export const api = {
  async getHealth() {
    const res = await fetch(`${API_BASE}/health`, { headers: getHeaders() });
    return res.json();
  },

  async uploadResume(file: File, targetRole?: string): Promise<ResumeData> {
    const formData = new FormData();
    formData.append('file', file);
    if (targetRole) formData.append('target_role', targetRole);
    const res = await fetch(`${API_BASE}/resume/upload`, {
      method: 'POST',
      headers: getHeaders(), // Don't set Content-Type for FormData, browser does it with boundary
      body: formData,
    });
    if (!res.ok) throw new Error('Resume parsing failed.');
    return res.json();
  },

  async matchJD(jobDescription: string, resumeSkills: string[], targetRole?: string): Promise<JDMatchResult> {
    const res = await fetch(`${API_BASE}/jd/match`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({
        job_description: jobDescription,
        resume_skills: resumeSkills,
        target_role: targetRole,
      }),
    });
    if (!res.ok) throw new Error('Failed to match JD.');
    return res.json();
  },

  async createSession(payload: {
    candidate_name: string;
    candidate_email: string;
    target_role: string;
    resume_text: string;
    job_description?: string;
  }): Promise<SessionInit> {
    const res = await fetch(`${API_BASE}/assessment/session`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify(payload),
    });
    if (!res.ok) throw new Error('Failed to create assessment session.');
    return res.json();
  },

  async startInterview(sessionId: string): Promise<{ session_id: string; current_question: QuestionData; stage: string }> {
    const res = await fetch(`${API_BASE}/assessment/${sessionId}/start`, { 
      method: 'POST',
      headers: getHeaders()
    });
    if (!res.ok) throw new Error('Failed to start interview.');
    return res.json();
  },

  async submitAnswer(sessionId: string, answerText: string): Promise<SubmitAnswerResult> {
    const res = await fetch(`${API_BASE}/assessment/${sessionId}/respond`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ answer_text: answerText }),
    });
    if (!res.ok) throw new Error('Failed to submit answer.');
    return res.json();
  },

  async getPracticalTask(sessionId: string): Promise<PracticalTask> {
    const res = await fetch(`${API_BASE}/assessment/${sessionId}/practical`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to load practical task.');
    return res.json();
  },

  async submitPractical(sessionId: string, code: string, language?: string): Promise<PracticalSubmitResult> {
    const res = await fetch(`${API_BASE}/assessment/${sessionId}/practical/submit`, {
      method: 'POST',
      headers: getHeaders({ 'Content-Type': 'application/json' }),
      body: JSON.stringify({ submission_code: code, language }),
    });
    if (!res.ok) throw new Error('Failed to evaluate practical submission.');
    return res.json();
  },

  async getSessionState(sessionId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/assessment/${sessionId}/state`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch session state.');
    return res.json();
  },

  async getFinalReport(sessionId: string): Promise<FinalReport> {
    const res = await fetch(`${API_BASE}/assessment/${sessionId}/report`, { headers: getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch final report.');
    return res.json();
  }
};
