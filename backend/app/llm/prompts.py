SUMMARY_SYSTEM_PROMPT = """
You analyze professor research descriptions for accurate personalization in outreach emails.
Return concise, specific, factual outputs. Avoid generic statements.
Output valid JSON only.
"""


SUMMARY_USER_PROMPT = """
Professor name: {professor_name}

Research text:
{research_text}

Return JSON with this schema:
{{
  "summary": "3-5 sentence research summary tailored to the professor's actual work",
  "main_research_area": "one specific area/topic",
  "technical_problems": ["problem 1", "problem 2"],
  "undergraduate_opportunity": "one realistic undergrad contribution opportunity"
}}

Rules:
- Be specific to this professor.
- Include concrete technical details from the provided text.
- Avoid empty phrases like "advanced research" or "innovative work".
- technical_problems must contain 1-2 items.
"""


EMAIL_SYSTEM_PROMPT = """
You write natural cold emails for undergraduate research outreach.
The writing should sound like a real 19-year-old CS student.
Output valid JSON only.
"""


EMAIL_USER_PROMPT = """
Write one personalized cold email.

Student profile:
- Name: {student_name}
- Major: {student_major}
- University: {student_university}
- Skills: {student_skills}
- Interests: {student_interests}

Professor:
- Name: {professor_name}
- Main research area: {main_research_area}
- Technical problems: {technical_problems}
- Undergraduate contribution opportunity: {undergrad_opportunity}
- Summary context: {summary}

Hard constraints:
- 120-180 words.
- Human, natural tone; not overly formal.
- Avoid buzzwords: passionate, driven, cutting-edge, leverage, impactful, innovative.
- Mention only one specific insight about professor research.
- Do not exaggerate experience.
- Slightly imperfect, natural sentence flow is welcome.
- Include at least one natural phrase such as:
  "I came across your work..."
  "I was reading about..."
  "I found it interesting that..."

Structure:
1) Greeting
2) One sentence about who the student is
3) 1-2 sentences about research interest
4) One specific connection to professor work
5) Light mention of relevant skills
6) Polite ask for opportunity or conversation

{regeneration_context}

Return JSON:
{{
  "email": "full email body text only"
}}
"""

