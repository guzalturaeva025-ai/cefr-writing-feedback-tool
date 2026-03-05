import streamlit as st
from groq import Groq
import requests
import pandas as pd

st.set_page_config(page_title="CEFR Writing Feedback Tool", layout="centered")

st.title("CEFR Writing Feedback Tool")

st.info("AI tool for evaluating student writing using CEFR criteria.")

# --- CHECK API KEY ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("Missing GROQ_API_KEY in Streamlit secrets.")
    st.stop()

api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# --- GOOGLE SCRIPT URL ---
url = "https://script.google.com/macros/s/AKfycbyISau2fk4hkekRR5-PGqoucUmz_xGK6mSDfnbikkN2z6R9uHHUzSEDYDF-ixU7STLbfA/exec"

# --- STUDENT INPUTS ---
student_name = st.text_input("Student Name")

level = st.selectbox(
    "CEFR Level",
    ["A1", "A2", "B1", "B2", "C1", "C2"]
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
        "Blog Post",
        "Complaint Letter",
        "Application Letter"
    ]
)

text = st.text_area("Student Writing", height=250)

# --- GENERATE FEEDBACK ---
if st.button("Generate Feedback"):

    if student_name.strip() == "":
        st.error("Please enter student name.")
        st.stop()

    if text.strip() == "":
        st.error("Please paste student writing.")
        st.stop()

    with st.spinner("Analyzing writing..."):

        prompt = f"""
You are a CEFR writing examiner.

Evaluate the following student writing at {level} level for a {genre}.

Provide:

1. Band score (4–1) for:
- Task Achievement
- Coherence & Organization
- Vocabulary Range & Control
- Grammatical Range & Accuracy
- Communicative Effectiveness

2. Short justification for each criterion.

3. Clear improvement suggestions.

Student Name: {student_name}

Student Text:
{text}
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        feedback = response.choices[0].message.content

        # --- SAVE TO GOOGLE SHEETS ---
        data = {
            "name": student_name,
            "level": level,
            "genre": genre,
            "text": text,
            "feedback": feedback
        }

        requests.post(url, data=data)

        st.success("Saved to Google Sheets")

        st.subheader("Feedback")
        st.write(feedback)

# --- TEACHER DASHBOARD ---
st.divider()
st.header("Teacher Dashboard")

try:
    response = requests.get(url)
    df = pd.DataFrame(response.json())

    if not df.empty:

        st.subheader("All Submissions")
        st.dataframe(df)

        col1, col2, col3 = st.columns(3)

        col1.metric("Total Submissions", len(df))
        col2.metric("Unique Students", df["Student Name"].nunique())
        col3.metric("Most Common Level", df["CEFR Level"].mode()[0])

    else:
        st.info("No submissions yet.")

except:
    st.warning("Could not load dashboard data yet.")
