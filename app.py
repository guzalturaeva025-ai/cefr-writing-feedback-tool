import streamlit as st
from groq import Groq
import requests

# --- PAGE CONFIG ---
st.set_page_config(page_title="CEFR Writing Feedback Tool", layout="centered")

st.title("CEFR Writing Feedback Tool")
st.write("Upload or paste your writing to receive structured CEFR-based feedback.")

# --- LOAD API KEY ---
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# --- GOOGLE SHEETS WEB APP URL ---
url = "https://script.google.com/macros/s/AKfycbwAJpnlax9dtHx8Z3tGSAH0gLTLUWb9p2SRgBdSER3SrBWFJGTs2eeS5GAf1LXab8AG/exec"

# --- USER INPUTS ---
level = st.selectbox("Select CEFR Level", ["A2", "B1", "B2", "C1"])
genre = st.selectbox("Select Genre", ["Essay", "Email", "Report", "Narrative"])

text = st.text_area(
    "Paste student writing here:",
    height=300,
    placeholder="Paste the student essay here..."
)

# --- GENERATE BUTTON ---
if st.button("Generate Feedback"):

    if text.strip() == "":
        st.error("Please paste student writing.")
        st.stop()

    with st.spinner("Analyzing writing..."):

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

        # --- AI RESPONSE ---
        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
            )

            feedback = response.choices[0].message.content

        except Exception as e:
            st.error("AI feedback could not be generated.")
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
            r = requests.post(url, data=data)

            if r.status_code == 200:
                st.success("✅ Response saved to Google Sheets.")
            else:
                st.warning("⚠️ Feedback generated but Google Sheets did not confirm saving.")

        except Exception as e:
            st.warning("⚠️ Feedback generated but data could not be saved.")
            st.write(e)

        # --- SHOW FEEDBACK ---
        st.divider()
        st.subheader("Feedback Report")
        st.write(feedback)
