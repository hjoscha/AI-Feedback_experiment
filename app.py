# ============================================================================
# AI Writing Feedback Agent - Streamlit App
# ============================================================================

import json
import random
from datetime import datetime

import streamlit as st
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials


# ----------------------------------------------------------------------------
# Page configuration
# ----------------------------------------------------------------------------

st.set_page_config(
    page_title="AI Writing Feedback Experiment",
    page_icon="✍️",
    layout="centered"
)


# ----------------------------------------------------------------------------
# Configure Gemini API
# ----------------------------------------------------------------------------

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel("gemini-2.5-flash")


# ----------------------------------------------------------------------------
# Configure Google Sheets
# ----------------------------------------------------------------------------

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive"
]

service_account_info = dict(st.secrets["GOOGLE_SERVICE_ACCOUNT"])

service_account_info["private_key"] = (
    service_account_info["private_key"]
    .replace("\\n", "\n")
)

creds = ServiceAccountCredentials.from_json_keyfile_dict(
    service_account_info,
    scope
)

client = gspread.authorize(creds)
sheet = client.open("AI_Feedback_Experiment").sheet1


# ----------------------------------------------------------------------------
# AI Writing Feedback Agent
# ----------------------------------------------------------------------------

class WritingFeedbackAgent:
    def __init__(self, gemini_model, feedback_strategy):
        self.feedback_strategy = feedback_strategy
        self.gemini = gemini_model

    def create_prompt(self, student_text, feedback_language):
        """
        Creates a reasoning-based pedagogical prompt depending on the assigned feedback strategy.
        """

        if self.feedback_strategy == "direct_corrective":
            
            prompt = f"""
            You are an AI writing tutor giving feedback to a language learner
            who is learning Dutch at B1 level.
            
            Your feedback strategy is direct corrective feedback.
            This means you identify errors and provide the corrected form immediately.
            You do not ask the learner to self-correct.
            
            The learner's proficiency level is B1 (intermediate).
            This means:
            - Use simple, clear language in your feedback.
            - Keep sentences short.
            - Do not use grammatical terminology unless it is very common
              (for example: "verb", "spelling", "sentence").
            - Do not overwhelm the learner with too many issues.
            
            Evaluate the text on:
            1. Grammatical accuracy
            2. Vocabulary use
            3. Spelling
            4. Coherence and organization
            5. Task completion
            
            For each issue:
            - Quote the exact phrase from the learner's text using "..."
            - Provide the corrected version
            - Add one short note (one sentence maximum) explaining what changed
            
            Focus only on the 4 to 6 most important issues.
            Prioritize errors that most affect comprehensibility.
            
            Structure your feedback EXACTLY as follows:
            
            [Label for general impression in the feedback language]: 
            [One short paragraph]
            
            "..." [quoted phrase from the learner]
            [Label for correction in the feedback language]: [corrected version]
            [Label for note in the feedback language]: [one sentence maximum]
            
            [Repeat the block above for each issue, 4 to 6 times]
            
            [Label for revision advice in the feedback language]:
            [One short paragraph with concrete revision advice]
            
            Constraints:
            - Write everything — including all labels and headings — in the
              following language: {feedback_language}
            - Plain text only. No markdown, no asterisks, no bullet symbols.
            - Short paragraphs, clearly separated.
            - No grade or score.
            - Do not mention the rubric by name.
            
            Student text:
            {student_text}
            """
        elif self.feedback_strategy == "explanatory":
            
            prompt = f"""
            You are an AI writing tutor giving feedback to a language learner
            who is learning Dutch at B1 level.
            
            Your feedback strategy is explanatory feedback.
            This means you identify errors, provide the corrected form, and
            explain in simple terms why the correction improves the sentence.
            The goal is for the learner to understand the reason behind the
            correction, not just see what the answer is.
            
            The learner's proficiency level is B1 (intermediate).
            This means:
            - Use simple, clear language in your feedback.
            - Keep sentences short.
            - Do not use grammatical terminology unless it is very common
              (for example: "verb", "spelling", "sentence").
            - Keep explanations brief — two sentences maximum per issue.
            - Do not overwhelm the learner with too many issues.
            
            Evaluate the text on:
            1. Grammatical accuracy
            2. Vocabulary use
            3. Spelling
            4. Coherence and organization
            5. Task completion
            
            For each issue:
            - Quote the exact phrase from the learner's text using "..."
            - Provide the corrected version
            - Explain briefly why the correction improves the sentence
            
            Focus only on the 4 to 6 most important issues.
            Prioritize issues where a short explanation genuinely adds understanding.
            
            Structure your feedback EXACTLY as follows:
            
            [Label for general impression in the feedback language]:
            [One short paragraph]
            
            "..." [quoted phrase from the learner]
            [Label for correction in the feedback language]: [corrected version]
            [Label for explanation in the feedback language]: [why this is better — two sentences maximum]
            
            [Repeat the block above for each issue, 4 to 6 times]
            
            [Label for revision advice in the feedback language]:
            [One short paragraph with concrete revision advice]
            
            Constraints:
            - Write everything — including all labels and headings — in the
              following language: {feedback_language}
            - Plain text only. No markdown, no asterisks, no bullet symbols.
            - Short paragraphs, clearly separated.
            - No grade or score.
            - Do not mention the rubric by name.
            
            Student text:
            {student_text}
            """

        elif self.feedback_strategy == "reflective":

            prompt = f"""
            You are an AI writing tutor giving feedback to a language learner
            who is learning Dutch at B1 level.
            
            Your feedback strategy is reflective feedback.
            This means you do not correct the learner's errors directly.
            Instead, you guide the learner to notice problems themselves
            by asking a short guiding question and giving a small hint.
            The learner should do the revision work themselves.
            
            The learner's proficiency level is B1 (intermediate).
            This means:
            - Use simple, clear language in your feedback.
            - Keep sentences short.
            - Questions and hints must be easy to understand.
            - Do not use grammatical terminology unless it is very common
              (for example: "verb", "spelling", "sentence").
            - Do not overwhelm the learner with too many issues.
            
            Evaluate the text on:
            1. Grammatical accuracy
            2. Vocabulary use
            3. Spelling
            4. Coherence and organization
            5. Task completion
            
            For each issue:
            - Quote the exact phrase from the learner's text using "..."
            - Ask one short guiding question to help the learner notice the problem
            - Give one short hint that points toward the solution
              without giving the full correction
            
            Focus only on the 4 to 6 most important issues.
            Do not rewrite the learner's sentences.
            Do not provide full corrected forms.
            
            Structure your feedback EXACTLY as follows:
            
            [Label for general impression in the feedback language]:
            [One short paragraph]
            
            "..." [quoted phrase from the learner]
            [Label for question in the feedback language]: [one guiding question]
            [Label for hint in the feedback language]: [one short hint, no full correction]
            
            [Repeat the block above for each issue, 4 to 6 times]
            
            [Label for revision advice in the feedback language]:
            [One short paragraph with encouragement and direction for revision]
            
            Constraints:
            - Write everything — including all labels and headings — in the
              following language: {feedback_language}
            - Plain text only. No markdown, no asterisks, no bullet symbols.
            - Short paragraphs, clearly separated.
            - No full corrections or rewritten sentences.
            - No grade or score.
            - Do not mention the rubric by name.
            
            Student text:
            {student_text}
            """
        else:
            raise ValueError("Invalid feedback strategy.")

        return prompt

    def generate_feedback(self, student_text, feedback_language):
        prompt = self.create_prompt(student_text, feedback_language)

        response = self.gemini.generate_content(prompt)
        return response.text


# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------

def assign_random_condition():
    conditions = ["direct_corrective", "explanatory", "reflective"]
    return random.choice(conditions)


def count_words(text):
    return len(text.split())


def save_to_google_sheets(
    participant_id,
    condition,
    feedback_language,
    pre_test_text,
    feedback,
    post_test_text,
    pre_word_count,
    post_word_count
):
    sheet.append_row([
        str(datetime.now()),
        participant_id,
        condition,
        feedback_language,
        pre_test_text,
        feedback,
        post_test_text,
        pre_word_count,
        post_word_count
    ])


# ----------------------------------------------------------------------------
# Session state
# ----------------------------------------------------------------------------

if "condition" not in st.session_state:
    st.session_state.condition = assign_random_condition()

if "feedback" not in st.session_state:
    st.session_state.feedback = None

if "pre_test_text" not in st.session_state:
    st.session_state.pre_test_text = ""

if "completed" not in st.session_state:
    st.session_state.completed = False


# ----------------------------------------------------------------------------
# App interface
# ----------------------------------------------------------------------------

st.title("AI Tutor Experiment")

st.write(
    """
    Welkom bij het experiment.

    Je voert twee korte schrijfopdrachten uit in het Nederlands. 
    Na de eerste opdracht ontvang je AI-gegenereerde feedback. 
    Na het lezen van de feedback schrijf je een tweede tekst.
    """
)

st.info(
    "Voer de opdrachten zelfstandig uit. Gebruik geen vertaaltools, AI-tools of andere externe hulpmiddelen."
)

participant_id = st.text_input("Participant ID")
feedback_language = st.text_input("Feedback taal", value="Nederlands")

st.divider()

st.header("Taak 1")
st.write(
    """
    Schrijf een tekst van ongeveer 100-150 woorden in het Nederlands.

    Onderwerp: Moet huiswerk onderdeel blijven van het onderwijs?

    Geef je mening en leg uit waarom.
    """
)

pre_test_text = st.text_area(
    "Schrijf je tekst hier",
    height=250,
    value=st.session_state.pre_test_text
)

pre_word_count = count_words(pre_test_text)
st.caption(f"Word count: {pre_word_count}. Om de word count te updaten kunt u naast het tekstvak klikken.")

if st.button("AI tutor feedback genereren"):
    if not participant_id.strip():
        st.error("Voer je participant ID in voordat je verdergaat..")
    elif pre_word_count < 80:
        st.error("Je tekst is te kort. Schrijf een langere tekst voordat je hem indient.")
    else:
        with st.spinner("Feedback genereren..."):
            agent = WritingFeedbackAgent(
                gemini_model=gemini_model,
                feedback_strategy=st.session_state.condition
            )

            st.session_state.feedback = agent.generate_feedback(
                student_text=pre_test_text,
                feedback_language=feedback_language
            )
            st.session_state.pre_test_text = pre_test_text


if st.session_state.feedback:
    st.divider()
    st.header("AI Tutor Feedback")
    st.text(st.session_state.feedback)

    st.divider()
    st.header("Taak 2")
    st.write(
        """
        Schrijf nu een NIEUWE tekst van ongeveer 100-150 woorden in het Nederlands.

        Onderwerp: Is online onderwijs goed voor studenten?

        Geef je mening en leg uit waarom.
        """
    )

    post_test_text = st.text_area(
        "Schrijf je tweede tekst hier",
        height=250
    )

    post_word_count = count_words(post_test_text)
    st.caption(f"Aantal woorden: {post_word_count}. Om de word count te updaten kunt u naast het tekstvak klikken.")

    if st.button("Experiment inleveren"):
        if post_word_count < 80:
            st.error("Je tekst is te kort. Schrijf een langere tekst voordat je hem indient.")
        else:
            save_to_google_sheets(
                participant_id=participant_id,
                condition=st.session_state.condition,
                feedback_language=feedback_language,
                pre_test_text=st.session_state.pre_test_text,
                feedback=st.session_state.feedback,
                post_test_text=post_test_text,
                pre_word_count=pre_word_count,
                post_word_count=post_word_count
            )

            st.session_state.completed = True
            st.success("Experiment klaar! U kunt terug naar de andere webpagina bovenaan uw scherm. Bedankt!")


if st.session_state.completed:
    st.balloons()
