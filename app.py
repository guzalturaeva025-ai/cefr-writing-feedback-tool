import streamlit as st
from groq import Groq
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="CEFR Writing Feedback Tool", layout="centered")

# --- APP INFO ---
st.info("This tool evaluates student writing using CEFR criteria and stores results in Google Sheets.")

st.title("CEFR Writing Feedback Tool")
st.write("Upload or paste your writing to receive structured CEFR-based feedback.")

# --- CHECK API KEY ---
if "GROQ_API_KEY" not in st.secrets:
    st.error("❌ GROQ_API_KEY is missing. Please add it in Streamlit Secrets.")
    st.stop()

# --- LOAD API KEY ---
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# --- GOOGLE SHEETS WEB APP URL ---
url = "https://script.google.com/macros/s/AKfycbyISau2fk4hkekRR5-PGqoucUmz_xGK6mSDfnbikkN2z6R9uHHUzSEDYDF-ixU7STLbfA/exec"

# --- INPUTS ---
level = st.selectbox("Select CEFR Level", ["A2", "B1", "B2", "C1"])
genre = st.selectbox("Select Genre", ["Essay", "Email", "Report", "Narrative"])
text = st.text_area("Paste student writing here:", height=300)

# --- GENERATE FEEDBACK ---
if st.button("Generate Feedback"):

    if text.strip() == "":
        st.error("Please paste student writing.")
        st.stop()

    with st.spinner("Generating feedback..."):

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

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            feedback = response.choices[0].message.content

        except Exception as e:
            st.error("Error generating feedback.")
            st.write(e)
            st.stop()

        # --- SEND DATA TO GOOGLE SHEETS ---
        data = {
            "level": level,
            "genre": genre,
            "text": text,
            "feedback": feedback
        }

        try:
            r = requests.post(url, data=data, timeout=10)

            if r.status_code == 200:
                st.success("✅ Saved to Google Sheets")
            else:
                st.warning(f"Feedback generated but saving failed. Status code: {r.status_code}")

        except requests.exceptions.RequestException as e:
            st.warning("Could not send data to Google Sheets.")
            st.write(e)

        # --- SHOW FEEDBACK ---
        st.subheader("Feedback Report")
        st.write(feedback)
