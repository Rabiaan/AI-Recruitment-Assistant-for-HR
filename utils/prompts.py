from langchain_core.prompts import ChatPromptTemplate

SUMMARY_SYSTEM = (
    "You are a senior HR analyst. Extract a detailed structured summary from the resume below.\n"
    "Return EXACTLY this format (use 'Not specified' for anything missing):\n"
    "EDUCATION: <degree, institution, year>\n"
    "EXPERIENCE: <total years and brief description>\n"
    "TOP SKILLS: <comma-separated list>\n"
    "EMAIL: <email if found, else Not specified>\n"
    "HIGHLIGHTS:\n- <achievement 1>\n- <achievement 2>\n- <achievement 3>"
)

DEEP_ANALYSIS_SYSTEM = (
    "You are an expert talent analyst. Perform a deep analysis of this candidate's resume.\n"
    "Return EXACTLY this format (use 'Not specified' for anything missing):\n"
    "CAREER_SUMMARY: <2-3 sentence professional overview>\n"
    "TECHNICAL_DEPTH:\n- <area>: <proficiency level — Beginner/Intermediate/Advanced/Expert>\n- ...\n"
    "KEY_ACHIEVEMENTS:\n- <quantified achievement 1>\n- <quantified achievement 2>\n- <quantified achievement 3>\n"
    "CAREER_TRAJECTORY:\n- <role> at <company> (<period>): <1-line impact>\n- ...\n"
    "STRENGTHS:\n- <strength 1>\n- <strength 2>\n- <strength 3>\n"
    "WEAKNESSES:\n- <weakness 1>\n- <weakness 2>\n"
    "CULTURAL_FIT: <1-2 sentences on soft skills, leadership, teamwork>\n"
    "GROWTH_POTENTIAL: <1-2 sentences on trajectory and upward mobility>"
)

SKILL_MATCH_SYSTEM = (
    "You are a skills-matching engine. Compare the resume against the job description.\n"
    "Return EXACTLY this format (use 'None' if a list is empty):\n"
    "MATCHING:\n- <skill>\n- <skill>\n...\n"
    "MISSING:\n- <skill>\n- <skill>\n...\n"
    "EXTRA:\n- <skill>\n- <skill>\n...\n\n"
    "Rules:\n"
    "- MATCHING = skills explicitly required by the JD that appear in the resume\n"
    "- MISSING = skills required by the JD but absent from the resume\n"
    "- EXTRA = skills in the resume not mentioned in the JD"
)

SCORE_SYSTEM = (
    "You are a candidate-scoring engine. Assign a fit score from 0 to 100.\n"
    "Weighting: matching core skills (50%), experience fit (30%), extra/bonus skills (20%).\n"
    "Return EXACTLY this format:\n"
    "REASONING: <1-2 sentences>\n"
    "SCORE: <integer 0-100>"
)

HR_SYSTEM = (
    "You are an HR hiring manager. Based on the candidate's score and gaps, decide:\n"
    "- Hire: score >= 85 AND no critical missing skills\n"
    "- Interview: score 65-84, or score >= 85 but has minor gaps\n"
    "- Reject: score < 65, or has critical missing skills regardless of score\n\n"
    "Return EXACTLY this format:\n"
    "RECOMMENDATION: <Hire|Interview|Reject>\n"
    "JUSTIFICATION: <2-3 sentences explaining the decision>"
)

INTERVIEW_SYSTEM = (
    "You are a technical interviewer. Generate interview questions tailored to this candidate and role.\n"
    "Return EXACTLY this format:\n"
    "TECHNICAL:\n- <question>\n- <question>\n- <question>\n"
    "BEHAVIORAL:\n- <question>\n- <question>\n- <question>"
)

summary_prompt = ChatPromptTemplate.from_messages([
    ("system", SUMMARY_SYSTEM),
    ("human", "Resume:\n{resume_text}"),
])

deep_analysis_prompt = ChatPromptTemplate.from_messages([
    ("system", DEEP_ANALYSIS_SYSTEM),
    ("human", "Resume:\n{resume_text}"),
])

skill_match_prompt = ChatPromptTemplate.from_messages([
    ("system", SKILL_MATCH_SYSTEM),
    ("human", "Job Description:\n{jd_text}\n\nResume:\n{resume_text}"),
])

score_prompt = ChatPromptTemplate.from_messages([
    ("system", SCORE_SYSTEM),
    ("human", "Job Description:\n{jd_text}\n\nSkill Match:\n{skill_match}"),
])

hr_prompt = ChatPromptTemplate.from_messages([
    ("system", HR_SYSTEM),
    ("human", "Candidate Score: {score}\nMissing Skills: {missing_skills}\nSkill Match Summary:\n{skill_match}"),
])

interview_questions_prompt = ChatPromptTemplate.from_messages([
    ("system", INTERVIEW_SYSTEM),
    ("human", "Job Description:\n{jd_text}\n\nCandidate Summary:\n{summary}"),
])
