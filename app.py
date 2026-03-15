import streamlit as st
from groq import Groq
import requests

st.set_page_config(page_title="CEFR Writing Feedback Tool", layout="centered")

st.title("CEFR Writing Feedback Tool")

# --- API ---
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# --- GOOGLE SCRIPT URL ---
url = "https://script.google.com/macros/s/AKfycbyyCLuWRVeSDMOwyj6PFVJH1Zry3PKIoJxDQQVwsCNQ3PVNixR_jrtT1jUdpVMrOj2wLQ/exec"

# --- INPUTS ---
student_name = st.text_input("Student Name")

level = st.selectbox(
    "CEFR Level",
    ["A1","A2","B1","B2","C1","C2"]
)

genre = st.selectbox(
    "Genre",
    [
        "Essay",
        "Opinion Essay",
        "For and Against Essay",
        "Email",
        "Formal Letter",
        "Informal Letter",
        "Report",
        "Article",
        "Review",
        "Narrative",
        "Story",
        "Blog Post"
    ]
)

text = st.text_area("Student Writing", height=300)

# --- BUTTON ---
if st.button("Generate Feedback"):

    # --- VALIDATION ---
    if not student_name.strip():
        st.error("Student name was empty. Please enter the student's name.")
        st.stop()

    if not text.strip():
        st.error("Student writing is empty.")
        st.stop()

    # --- WORD COUNT ---
    wordcount = len(text.split())

    # --- CEFR FEEDBACK PROMPT ---
    prompt = f"""
You are a CEFR writing examiner.

Evaluate the student's writing at {level} level for a {genre}.

IMPORTANT RULES:
- Do NOT rewrite the student's essay.
- Do NOT continue the essay.
- Do NOT correct the essay line by line.
- Only evaluate and give feedback.

Provide:

1. Band score (1–4) for:
Task Achievement
Coherence & Organization
Vocabulary Range
Grammatical Range & Accuracy
Communicative Effectiveness

2. Brief explanation for each score.

3. General improvement suggestions (do not rewrite the essay).

Student Text:
{text}
"""

    # --- GENERATE FEEDBACK ---
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        feedback = response.choices[0].message.content

    except Exception as e:
        st.error("AI feedback generation failed.")
        st.stop()

    # --- ERROR CORRECTION PROMPT ---
    error_prompt = f"""
You are an English teacher.

Analyze the student's text and identify grammar, vocabulary, and spelling mistakes.

Show mistakes in this format:

incorrect → correction (short explanation)

Example:
go → went (past tense)

Rules:
- Do NOT rewrite the full essay
- Do NOT continue the essay
- Only list the mistakes and corrections
- Be concise

Student Text:
{text}
"""

    # --- GENERATE CORRECTIONS ---
    try:
        error_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":error_prompt}],
            temperature=0.2,
        )

        error_feedback = error_response.choices[0].message.content

    except Exception as e:
        st.error("Error correction generation failed.")
        st.stop()

    # --- DATA TO GOOGLE SHEETS ---
    data = {
        "name": student_name,
        "level": level,
        "genre": genre,
        "wordcount": wordcount,
        "text": text,
        "feedback": feedback,
        "corrections": error_feedback
    }

    try:
        r = requests.post(url, data=data)

        if r.status_code == 200:
            st.success("Saved to Google Sheets")

    except:
        st.warning("Could not save to Google Sheets")

    # --- DISPLAY RESULTS ---
    st.subheader("CEFR Feedback")
    st.write(feedback)

    st.subheader("Error Correction")
    st.write(error_feedback)
