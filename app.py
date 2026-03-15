import streamlit as st
from groq import Groq
import requests
import statistics

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
        st.error("Student name was empty.")
        st.stop()

    if not text.strip():
        st.error("Student writing is empty.")
        st.stop()

    # --- BASIC METRICS ---
    wordcount = len(text.split())

    sentences = text.split(".")
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

    avg_sentence_length = round(sum(sentence_lengths)/len(sentence_lengths),2) if sentence_lengths else 0
    sentence_variation = round(statistics.pstdev(sentence_lengths),2) if len(sentence_lengths) > 1 else 0

    unique_words = len(set(text.lower().split()))
    lexical_diversity = round(unique_words/wordcount,2) if wordcount > 0 else 0

    # --- CEFR FEEDBACK PROMPT ---
    prompt = f"""
You are a CEFR writing examiner.

Evaluate the student's writing at {level} level for a {genre}.

IMPORTANT RULES:
- Do NOT rewrite the student's essay
- Do NOT continue the essay
- Do NOT correct line by line
- Only evaluate and give feedback

Provide:

1. Band score (1–4) for:
Task Achievement
Coherence & Organization
Vocabulary Range
Grammatical Range & Accuracy
Communicative Effectiveness

2. Brief explanation for each score.

3. General improvement suggestions.

Student Text:
{text}
"""

    # --- GENERATE FEEDBACK ---
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":prompt}],
            temperature=0.7,
        )

        feedback = response.choices[0].message.content

    except:
        st.error("AI feedback generation failed.")
        st.stop()

    # --- ERROR CORRECTION PROMPT ---
    error_prompt = f"""
You are an English teacher.

Identify grammar, vocabulary and spelling mistakes.

Show corrections in this format:

incorrect → correction (short explanation)

Example:
go → went (past tense)

Rules:
- Do NOT rewrite the essay
- Only list mistakes

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

    except:
        st.error("Error correction generation failed.")
        st.stop()

    # --- AI DETECTION PROMPT ---
    ai_prompt = f"""
You are an academic writing analyst.

Estimate the likelihood that the text was written by AI.

Provide:

1. AI likelihood score (0–100%)
2. Indicators supporting the judgement
3. Writing characteristics noticed

Important: this is probabilistic and not definitive.

Text:
{text}
"""

    # --- GENERATE AI DETECTION ---
    try:
        ai_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role":"user","content":ai_prompt}],
            temperature=0.2,
        )

        ai_detection = ai_response.choices[0].message.content

    except:
        ai_detection = "AI detection unavailable."

    # --- SAVE DATA TO GOOGLE SHEETS ---
    data = {
        "name": student_name,
        "level": level,
        "genre": genre,
        "wordcount": wordcount,
        "avg_sentence_length": avg_sentence_length,
        "sentence_variation": sentence_variation,
        "lexical_diversity": lexical_diversity,
        "text": text,
        "feedback": feedback,
        "corrections": error_feedback,
        "ai_detection": ai_detection
    }

    try:
        r = requests.post(url, data=data)

        if r.status_code == 200:
            st.success("Saved to Google Sheets")

    except:
        st.warning("Could not save to Google Sheets")

    # --- DISPLAY RESULTS ---

    st.subheader("Writing Statistics")

    st.write(f"Word Count: {wordcount}")
    st.write(f"Average Sentence Length: {avg_sentence_length}")
    st.write(f"Sentence Variation (Burstiness): {sentence_variation}")
    st.write(f"Lexical Diversity: {lexical_diversity}")

    st.subheader("CEFR Feedback")
    st.markdown(feedback)

    st.subheader("Error Correction")
    st.markdown(error_feedback)

    st.subheader("AI Writing Likelihood")
    st.markdown(ai_detection)

    st.caption("AI detection is probabilistic and cannot guarantee authorship.")
