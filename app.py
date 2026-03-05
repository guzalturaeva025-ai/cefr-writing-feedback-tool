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
    if not student_name or student_name.strip() == "":
        st.error("Student name was empty. Please enter the student's name.")
        st.stop()

    if not text or text.strip() == "":
        st.error("Student writing is empty.")
        st.stop()

    # --- WORD COUNT ---
    wordcount = len(text.split())

    # --- PROMPT ---
    prompt = f"""
You are a CEFR writing examiner.

Evaluate the following writing at {level} level for a {genre}.

Provide scores (1–4) for:

Task Achievement
Coherence & Organization
Vocabulary Range
Grammar Accuracy
Communicative Effectiveness

Then give improvement suggestions.

Text:
{text}
"""

    # --- AI RESPONSE ---
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
    )

    feedback = response.choices[0].message.content

    # --- DATA TO GOOGLE SHEETS ---
    data = {
        "name": student_name,
        "level": level,
        "genre": genre,
        "wordcount": wordcount,
        "text": text,
        "feedback": feedback
    }

    try:
        r = requests.post(url, data=data)

        if r.status_code == 200:
            st.success("Saved to Google Sheets")

    except:
        st.warning("Could not save to Google Sheets")

    # --- DISPLAY ---
    st.subheader("Feedback")
    st.write(feedback)

