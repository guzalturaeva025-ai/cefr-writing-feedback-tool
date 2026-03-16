import streamlit as st
import streamlit.components.v1 as components
from groq import Groq
import requests
import statistics
import re

st.set_page_config(page_title="CEFR Writing Feedback Tool", layout="centered")

# --- Disable browser typing helpers ---
st.markdown("""
<style>

textarea {
    autocomplete: off !important;
    autocorrect: off !important;
    autocapitalize: off !important;
    spellcheck: false !important;

    -webkit-user-modify: read-write-plaintext-only;
    text-rendering: optimizeSpeed;
}

textarea::-webkit-contacts-auto-fill-button,
textarea::-webkit-credentials-auto-fill-button {
    visibility: hidden;
    display: none !important;
}

textarea::spelling-error {
    text-decoration: none;
}

textarea::grammar-error {
    text-decoration: none;
}

</style>
""", unsafe_allow_html=True)

st.title("CEFR Writing Feedback Tool")

st.info("Please disable AI writing assistants and browser predictions before completing this task.")

# --- API ---
api_key = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=api_key)

# --- GOOGLE SCRIPT URL ---
url = "https://script.google.com/macros/s/AKfycbxi-8EH2eNX8EpLuWqzd73S0exRS9iufOnfiana4U-CeGMhA5Wcafo09reCEK4f724G/exec"

# --- CEFR vocabulary lists ---
A1_words = {"go","come","make","take","see","know","think","want","like","play"}
A2_words = {"decide","improve","travel","learn","study","teach","build"}
B1_words = {"achieve","benefit","suggest","develop","support"}
B2_words = {"significant","impact","approach","complex","maintain"}
C1_words = {"comprehensive","substantial","evaluate","interpret"}
C2_words = {"paradigm","intrinsic","nuanced"}

# --- INPUTS ---
student_name = st.text_input("Student Name")

level = st.selectbox("CEFR Level", ["A1","A2","B1","B2","C1","C2"])

genre = st.selectbox(
    "Genre",
    [
        "Essay","Opinion Essay","For and Against Essay","Email",
        "Formal Letter","Informal Letter","Report","Article",
        "Review","Narrative","Story","Blog Post"
    ]
)

# --- Custom writing box ---
essay_text = components.html(
"""
<textarea id="essay"
autocomplete="off"
autocorrect="off"
autocapitalize="off"
spellcheck="false"
style="width:100%;height:300px;padding:12px;font-size:16px;border:2px solid #ddd;border-radius:8px;font-family:Arial;"
></textarea>

<script>

const textarea = document.getElementById("essay");

textarea.addEventListener("keydown", function(e){
    if(e.key === "Tab"){
        e.preventDefault();
    }
});

textarea.addEventListener("input", function(){
    const value = textarea.value;
    window.parent.postMessage(
        {type: "streamlit:setComponentValue", value: value},
        "*"
    );
});

</script>
""",
height=320,
)

text = essay_text or ""

# --- BUTTON ---
if st.button("Generate Feedback"):

   # --- VALIDATION ---
if not student_name.strip():
    st.error("Student name was empty.")
    st.stop()

if not text or not text.strip():
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

    # --- BURSTINESS & ORIGINALITY ---
    burstiness = sentence_variation
    repetition_ratio = 1 - lexical_diversity

    # --- CEFR VOCAB ANALYSIS ---
    words = re.findall(r'\b\w+\b', text.lower())

    A1_count = sum(1 for w in words if w in A1_words)
    A2_count = sum(1 for w in words if w in A2_words)
    B1_count = sum(1 for w in words if w in B1_words)
    B2_count = sum(1 for w in words if w in B2_words)
    C1_count = sum(1 for w in words if w in C1_words)
    C2_count = sum(1 for w in words if w in C2_words)

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

Mark mistakes directly in the text.

Format:
[word → correction]

Example:
I go [→ went] to school yesterday.

Text:
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
        "burstiness": burstiness,
        "repetition_ratio": repetition_ratio,
        "A1_words": A1_count,
        "A2_words": A2_count,
        "B1_words": B1_count,
        "B2_words": B2_count,
        "C1_words": C1_count,
        "C2_words": C2_count,
        "text": text,
        "feedback": feedback,
        "corrections": error_feedback,
        "ai_detection": ai_detection
    }

    try:
        r = requests.post(url, json=data)

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

    st.subheader("CEFR Vocabulary Usage")

    st.write(f"A1 words: {A1_count}")
    st.write(f"A2 words: {A2_count}")
    st.write(f"B1 words: {B1_count}")
    st.write(f"B2 words: {B2_count}")
    st.write(f"C1 words: {C1_count}")
    st.write(f"C2 words: {C2_count}")

    st.subheader("Originality Indicator")

    if repetition_ratio > 0.6:
        st.warning("High repetition detected. Possible copied or AI-generated patterns.")
    else:
        st.success("Writing shows reasonable lexical variation.")

    st.subheader("Writing Pattern Analysis")

    if burstiness < 3:
        st.write("Low burstiness: writing may resemble AI style.")
    else:
        st.write("Higher burstiness: writing resembles human variability.")

    st.subheader("CEFR Feedback")
    st.markdown(feedback)

    st.subheader("Annotated Essay")
    st.markdown(error_feedback)

    st.subheader("AI Writing Likelihood")
    st.markdown(ai_detection)

    st.caption("AI detection is probabilistic and cannot guarantee authorship.")
