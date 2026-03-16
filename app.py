import streamlit as st
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
}
</style>
""", unsafe_allow_html=True)

st.title("CEFR Writing Feedback Tool")

st.warning(
"⚠️ Important: Please write your text independently. AI writing assistants, autocomplete suggestions, and pasted text may be detected by the system."
)
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

level = st.selectbox(
    "CEFR Level",
    ["A1","A2","B1","B2","C1","C2"]
)

genre = st.selectbox(
    "Genre",
    [
        "Essay","Opinion Essay","For and Against Essay","Email",
        "Formal Letter","Informal Letter","Report","Article",
        "Review","Narrative","Story","Blog Post"
    ]
)

# --- Student Writing ---
text = st.text_area(
    "Write your essay here...",
    height=330,
    placeholder="Write your essay here..."
)

st.markdown("""
<script>
const textarea = window.parent.document.querySelector('textarea');

if (textarea) {

    // disable TAB suggestion acceptance
    textarea.addEventListener("keydown", function(e){
        if (e.key === "Tab"){
            e.preventDefault();
        }
    });

    // disable paste
    textarea.addEventListener("paste", function(e){
        e.preventDefault();
    });

    // disable right click
    textarea.addEventListener("contextmenu", function(e){
        e.preventDefault();
    });

}
</script>
""", unsafe_allow_html=True)

# --- BUTTON ---
if st.button("Generate Feedback"):

    if text.strip() == "":
        st.warning("Please enter your essay before generating feedback.")
        st.stop()

    # --- WORD COUNT ---
    wordcount = len(text.split())
    st.write("Word count:", wordcount)

    # --- BASIC METRICS ---
    sentences = text.split(".")
    sentence_lengths = [len(s.split()) for s in sentences if s.strip()]

    if sentence_lengths:
        avg_sentence_length = round(sum(sentence_lengths) / len(sentence_lengths), 2)
    else:
        avg_sentence_length = 0

    if len(sentence_lengths) > 1:
        sentence_variation = round(statistics.pstdev(sentence_lengths), 2)
    else:
        sentence_variation = 0

    st.write("Average sentence length:", avg_sentence_length)
    st.write("Sentence variation:", sentence_variation)

    unique_words = len(set(text.lower().split()))
    lexical_diversity = round(unique_words / wordcount, 2) if wordcount > 0 else 0

    burstiness = sentence_variation
    repetition_rate = 1 - lexical_diversity

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

Provide band scores and suggestions.

Student Text:
{text}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":prompt}],
        temperature=0.7,
    )

    feedback = response.choices[0].message.content

    # --- ERROR CORRECTION PROMPT ---
    error_prompt = f"""
You are an English teacher.

Mark mistakes directly in the text.

Format:
[word → correction]

Text:
{text}
"""

    error_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":error_prompt}],
        temperature=0.2,
    )

    corrections = error_response.choices[0].message.content

    # --- AI DETECTION PROMPT ---
    ai_prompt = f"""
Estimate likelihood that the text was written by AI.

Text:
{text}
"""

    ai_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role":"user","content":ai_prompt}],
        temperature=0.2,
    )

    ai_detection = ai_response.choices[0].message.content

  sentence_variation,
        "lexical_diversity": lexical_diversity,
        "burstiness": burstiness,
        "repetition_rate": repetition_rate
    }

    try:
        response = requests.post(url, json=data)

        if response.status_code == 200:
            st.success("Results saved to Google Sheets")
        else:
            st.error("Google Sheets connection failed")

    except Exception as e:
        st.error(f"Error sending data: {e}")

    # --- DISPLAY RESULTS ---
    st.subheader("Writing Statistics")
    st.write(f"Word Count: {wordcount}")
    st.write(f"Average Sentence Length: {avg_sentence_length}")
    st.write(f"Sentence Variation: {sentence_variation}")
    st.write(f"Lexical Diversity: {lexical_diversity}")

    st.subheader("CEFR Vocabulary Usage")
    st.write(f"A1 words: {A1_count}")
    st.write(f"A2 words: {A2_count}")
    st.write(f"B1 words: {B1_count}")
    st.write(f"B2 words: {B2_count}")
    st.write(f"C1 words: {C1_count}")
    st.write(f"C2 words: {C2_count}")

    st.subheader("CEFR Feedback")
    st.markdown(feedback)

    st.subheader("Annotated Essay")
    st.markdown(corrections)

    st.subheader("AI Writing Likelihood")
    st.markdown(ai_detection)
