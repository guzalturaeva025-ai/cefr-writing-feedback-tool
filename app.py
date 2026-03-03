import streamlit as st
from openai import OpenAI

# --- CONFIG ---
st.set_page_config(page_title="CEFR Writing Feedback Tool", layout="centered")

st.title("CEFR Writing Feedback Tool")
st.write("Upload or paste your writing to receive structured CEFR-based feedback.")

# --- INPUTS ---
level = st.selectbox("Select CEFR Level", ["A2", "B1", "B2", "C1"])
genre = st.selectbox("Select Genre", ["Essay", "Email", "Report", "Narrative"])

text = st.text_area("Paste student writing here:", height=300)

api_key = st.text_input("Enter your OpenAI API Key", type="password")

# --- FEEDBACK LOGIC ---
if st.button("Generate Feedback"):

    if not api_key:
        st.error("Please enter your OpenAI API key.")
    elif not text:
        st.error("Please paste student writing.")
    else:
        client = OpenAI(api_key=api_key)

        prompt = f"""
You are a CEFR writing examiner.

Evaluate the following student writing at {level} level for a {genre}.

Provide:

1. Band score (4-1) for:
   - Task Achievement
   - Coherence & Organization
   - Vocabulary Range & Control
   - Grammatical Range & Accuracy
   - Communicative Effectiveness

2. Short justification for each criterion.

3. Clear improvement suggestions.

Student Text:
{text}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        feedback = response.choices[0].message.content
        st.subheader("Feedback Report")
        st.write(feedback)