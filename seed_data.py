"""Seed script: pushes sample data directly to Supabase (no AI calls)."""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from utils.pdf_reader import extract_text
from ai.db import insert_job_description, insert_candidate_result


JD_FILES = [
    "data/Senior_Python_Developer_JD.pdf",
    "data/AI_Engineer_JD.pdf",
]

RESUME_FILES = [
    "data/John_Doe.pdf",
    "data/Jane_Smith.pdf",
    "data/Alice_Johnson.pdf",
    "data/Bob_Williams.pdf",
    "data/Carol_Brown.pdf",
]


def extract_pdf(path):
    with open(path, "rb") as f:
        result = extract_text(f)
    if result.success:
        print(f"  [OK] {os.path.basename(path)} -> {result.page_count} pages, {len(result.text)} chars")
        return result.text
    else:
        print(f"  [FAIL] {os.path.basename(path)} -> {result.warning}")
        return None


def main():
    print("=" * 60)
    print("SEED: Extracting PDFs")
    print("=" * 60)

    jd_texts = {}
    for path in JD_FILES:
        if os.path.exists(path):
            text = extract_pdf(path)
            if text:
                jd_texts[path] = text

    resume_texts = {}
    for path in RESUME_FILES:
        if os.path.exists(path):
            text = extract_pdf(path)
            if text:
                resume_texts[path] = text

    if not jd_texts:
        print("\nNo JD texts extracted. Aborting.")
        return

    primary_jd_path = list(jd_texts.keys())[0]
    jd_text = jd_texts[primary_jd_path]

    print(f"\nUsing JD: {primary_jd_path}")
    print("\n" + "=" * 60)
    print("SEED: Pushing to Supabase")
    print("=" * 60)

    try:
        jd_row = insert_job_description(title="Senior Python Developer", raw_text=jd_text)
        jd_id = jd_row.get("id", "")
        print(f"  JD inserted: {jd_id}")

        for path, text in resume_texts.items():
            name = os.path.splitext(os.path.basename(path))[0].replace("_", " ")

            lines = text.split("\n")
            email = "Not specified"
            for line in lines:
                if "@" in line and "." in line:
                    for word in line.split():
                        if "@" in word and "." in word:
                            email = word.strip("(),;")
                            break
                    break

            skills = []
            skill_keywords = ["python", "java", "react", "fastapi", "django", "postgresql",
                              "docker", "kubernetes", "aws", "tensorflow", "pytorch", "nlp",
                              "nodejs", "typescript", "javascript", "terraform", "ansible",
                              "redis", "ci/cd", "git", "linux", "bash", "sql", "pandas",
                              "scikit-learn", "rest-api", "agile", "gitlab-ci"]
            text_lower = text.lower()
            for kw in skill_keywords:
                if kw in text_lower:
                    skills.append(kw)

            experience_years = 3
            exp_match = None
            import re
            for pat in [r"(\d+)\+?\s*years?", r"(\d+)\+?\s*yr"]:
                exp_match = re.search(pat, text, re.IGNORECASE)
                if exp_match:
                    experience_years = int(exp_match.group(1))
                    break

            score = min(60 + len(skills) * 3, 95)
            if score >= 85:
                rec, justification = "Hire", f"Strong candidate with {len(skills)} matching skills and {experience_years} years experience."
            elif score >= 65:
                rec, justification = "Interview", f"Good fit with {len(skills)} relevant skills. Worth interviewing."
            else:
                rec, justification = "Reject", f"Limited skill overlap. Only {len(skills)} matching skills found."

            matching = skills[:len(skills)//2 + 1] if skills else ["General"]
            missing = [s for s in skill_keywords[:8] if s not in skills][:3]
            extra = [s for s in skills if s not in skill_keywords[:8]][:3]

            row = insert_candidate_result(
                jd_id=jd_id,
                candidate_name=name,
                resume_text=text,
                summary=text[:500],
                education="Not specified",
                experience_years=experience_years,
                matching_skills=matching,
                missing_skills=missing,
                extra_skills=extra,
                score=score,
                recommendation=rec,
                justification=justification,
                technical_questions=[],
                hr_questions=[],
                status="Sourced",
                email=email,
                career_summary=text[:300],
                technical_depth=[f"{s}: Intermediate" for s in matching[:4]],
                key_achievements=["Built scalable systems", "Led team projects", "Optimized performance"],
                career_trajectory=[f"Developer at Tech Corp ({experience_years} years): Worked on backend systems"],
                ai_strengths=matching[:3] or ["Technical skills"],
                ai_weaknesses=missing[:2] or ["Needs evaluation"],
                cultural_fit="Team player with good communication skills",
                growth_potential="Shows upward trajectory with consistent skill development",
            )
            print(f"  + {name} | score={score} | rec={rec} | id={row.get('id', 'N/A')[:8]}")

        print(f"\nDone! {len(resume_texts)} candidates seeded.")
    except Exception as e:
        print(f"\nSupabase insert failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
