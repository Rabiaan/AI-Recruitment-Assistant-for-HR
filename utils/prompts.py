from langchain_core.prompts import ChatPromptTemplate

EXTRACT_SYSTEM = (
    "You are a senior HR analyst. Extract ALL structured data from this resume in a single pass.\n"
    "Return EXACTLY this format (use 'Not specified' for anything missing, empty list for missing lists):\n\n"
    "EDUCATION: <degree, institution, year>\n"
    "EXPERIENCE_YEARS: <total years as number>\n"
    "EMAIL: <email if found, else Not specified>\n"
    "CAREER_SUMMARY: <2-3 sentence professional overview>\n"
    "TOP_SKILLS: <comma-separated list of all technical and professional skills>\n\n"
    "TECHNICAL_DEPTH:\n- <area>: <proficiency level — Beginner/Intermediate/Advanced/Expert>\n- ...\n\n"
    "KEY_ACHIEVEMENTS:\n- <quantified achievement 1>\n- <quantified achievement 2>\n- <quantified achievement 3>\n\n"
    "CAREER_TRAJECTORY:\n- <role> at <company> (<period>): <1-line impact>\n- ...\n\n"
    "STRENGTHS:\n- <strength 1>\n- <strength 2>\n- <strength 3>\n\n"
    "WEAKNESSES:\n- <weakness 1>\n- <weakness 2>\n\n"
    "CULTURAL_FIT: <1-2 sentences on soft skills, leadership, teamwork>\n"
    "GROWTH_POTENTIAL: <1-2 sentences on trajectory and upward mobility>"
)

ANALYZE_SYSTEM = (
    "You are an expert hiring panel. Given the extracted candidate data and the job description, perform a complete assessment.\n"
    "Return EXACTLY this format:\n\n"
    "MATCHING:\n- <skill from JD found in candidate>\n- ...\n\n"
    "MISSING:\n- <skill from JD NOT found in candidate>\n- ...\n\n"
    "EXTRA:\n- <skill in candidate NOT in JD>\n- ...\n\n"
    "SCORE: <integer 0-100, weighted: matching skills 50%, experience fit 30%, bonus skills 20%>\n\n"
    "RECOMMENDATION: <Hire|Interview|Reject>\n"
    "- Hire: score >= 85 AND no critical missing skills\n"
    "- Interview: score 65-84, or score >= 85 but has minor gaps\n"
    "- Reject: score < 65, or critical missing skills\n\n"
    "JUSTIFICATION: <2-3 sentences explaining the decision>"
)

INTERVIEW_SYSTEM = (
    "You are a technical interviewer. Generate interview questions tailored to this candidate and role.\n"
    "Return EXACTLY this format:\n"
    "TECHNICAL:\n- <question>\n- <question>\n- <question>\n"
    "BEHAVIORAL:\n- <question>\n- <question>\n- <question>"
)

extract_prompt = ChatPromptTemplate.from_messages([
    ("system", EXTRACT_SYSTEM),
    ("human", "Resume:\n{resume_text}"),
])

analyze_prompt = ChatPromptTemplate.from_messages([
    ("system", ANALYZE_SYSTEM),
    ("human", "Job Description:\n{jd_text}\n\nCandidate Extracted Data:\n{extracted_data}"),
])

interview_questions_prompt = ChatPromptTemplate.from_messages([
    ("system", INTERVIEW_SYSTEM),
    ("human", "Job Description:\n{jd_text}\n\nCandidate Summary:\n{summary}"),
])
