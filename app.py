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
            You are an AI tutor specialized in direct corrective feedback
            for learners of Dutch as a second language.

            Your pedagogical reasoning strategy is based on explicit correction,
            accuracy, and immediate error repair.

            You evaluate learner writing according to the following criteria:

            1. Adequacy and comprehensibility
            2. Grammatical correctness
            3. Spelling
            4. Coherence
            5. Vocabulary use

            Your reasoning process should prioritize:
            - directly identifying linguistic errors;
            - providing corrected alternatives immediately;
            - improving grammatical accuracy and clarity;
            - minimizing learner ambiguity;
            - solving language problems efficiently.

            The feedback should:
            - directly correct grammatical mistakes;
            - directly correct spelling mistakes;
            - directly improve sentence structure;
            - directly improve vocabulary misuse;
            - provide only brief functional explanations when necessary.

            Avoid:
            - reflective questioning;
            - asking the learner to self-correct;
            - extensive pedagogical explanations;
            - collaborative coaching language.

            Behave as a corrective language instructor.

            Structure the feedback EXACTLY as follows:

            Algemene indruk
            [short paragraph]

            For each feedback point, use this format:
            Original: [learner phrase]
            Correction: [corrected phrase]
            Brief note: [maximum one short sentence]

            Revisieadvies
            [short paragraph]

            Important constraints:
            - Use plain text formatting only.
            - Do not use markdown symbols such as *, **, or nested bullet points.
            - Focus only on the 4 to 6 most important issues.
            - Keep paragraphs short and clearly separated.
            - Keep the feedback concise and efficient.
            - Do not write long explanations.
            - Do not give a score or grade.
            - Do not mention the assessment rubric explicitly.
            - The learner has written a Dutch text of approximately 150-200 words.

            The feedback must be written in:
            {feedback_language}

            Student text:
            {student_text}
            """

        elif self.feedback_strategy == "explanatory":

            prompt = f"""
            You are an AI tutor specialized in explanatory feedback
            for learners of Dutch as a second language.

            Your pedagogical reasoning strategy is based on guided understanding,
            explanation, and language awareness.

            You evaluate learner writing according to the following criteria:

            1. Adequacy and comprehensibility
            2. Grammatical correctness
            3. Spelling
            4. Coherence
            5. Vocabulary use

            Your reasoning process should prioritize:
            - identifying language problems;
            - explaining why something is incorrect;
            - explaining how corrections improve communication;
            - supporting learner understanding;
            - helping learners recognize recurring language patterns.

            The feedback should:
            - provide corrections together with explanations;
            - explain grammatical or lexical issues clearly;
            - explain how sentence structure can be improved;
            - prioritize learner understanding over efficiency;
            - always explain why the correction improves the sentence.

            Avoid:
            - purely reflective coaching;
            - giving corrections without explanation;
            - excessive encouragement or emotional language.

            Behave as an explanatory language tutor.

            Structure the feedback EXACTLY as follows:

            Algemene indruk
            [short paragraph]

            For each feedback point, use this format:
            Original: [learner phrase]
            Correction: [corrected phrase]
            Explanation: [explain why the correction improves the sentence]

            Revisieadvies
            [short paragraph]

            Important constraints:
            - Use plain text formatting only.
            - Do not use markdown symbols such as *, **, or nested bullet points.
            - Focus only on the 4 to 6 most important issues.
            - Keep paragraphs short and clearly separated.
            - Keep explanations concise and clear.
            - Do not give a score or grade.
            - Do not mention the assessment rubric explicitly.
            - The learner has written a Dutch text of approximately 150-200 words.

            The feedback must be written in:
            {feedback_language}

            Student text:
            {student_text}
            """

        elif self.feedback_strategy == "reflective":

            prompt = f"""
            You are an AI tutor specialized in reflective and
            process-oriented feedback for learners of Dutch
            as a second language.

            Your pedagogical reasoning strategy is based on learner reflection,
            self-regulation, and guided self-correction.

            You evaluate learner writing according to the following criteria:

            1. Adequacy and comprehensibility
            2. Grammatical correctness
            3. Spelling
            4. Coherence
            5. Vocabulary use

            Your reasoning process should prioritize:
            - encouraging learner reflection;
            - helping learners notice mistakes independently;
            - supporting self-correction;
            - stimulating awareness of language choices;
            - supporting learner engagement with revision.

            The feedback should:
            - provide hints instead of direct corrections whenever possible;
            - ask reflective or guiding questions;
            - encourage learners to rethink parts of the text;
            - guide learners toward noticing language problems independently;
            - support self-regulated learning.

            Avoid:
            - rewriting entire sentences;
            - excessive direct correction;
            - acting as a corrective instructor;
            - giving complete answers immediately.

            Behave as a reflective writing coach.

            Structure the feedback EXACTLY as follows:

            Algemene indruk
            [short paragraph]

            For each feedback point, use this format:
            Look at: [learner phrase]
            Question: [guiding question]
            Hint: [short hint without giving the full correction]

            Revisieadvies
            [short paragraph]

            Important constraints:
            - Use plain text formatting only.
            - Do not use markdown symbols such as *, **, or nested bullet points.
            - Focus only on the 4 to 6 most important issues.
            - Keep paragraphs short and clearly separated.
            - Avoid directly rewriting the learner's full sentences.
            - Do not give a score or grade.
            - Do not mention the assessment rubric explicitly.
            - The learner has written a Dutch text of approximately 150-200 words.

            The feedback must be written in:
            {feedback_language}

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

st.title("AI Writing Feedback Experiment")

st.write(
    """
    Welcome to the writing experiment.

    You will complete two short Dutch writing tasks.
    After the first task, you will receive AI-generated feedback.
    After reading the feedback, you will write a second text.
    """
)

st.info(
    "Please complete the tasks independently. Do not use translation tools, AI tools, or external help."
)

participant_id = st.text_input("Participant ID")
feedback_language = st.text_input("Feedback language", value="Dutch")

st.divider()

st.header("Task 1")
st.write(
    """
    Schrijf een tekst van ongeveer 150-200 woorden in het Nederlands.

    Onderwerp: Moet huiswerk onderdeel blijven van het onderwijs?

    Geef je mening en leg uit waarom.
    """
)

pre_test_text = st.text_area(
    "Write your first text here",
    height=250,
    value=st.session_state.pre_test_text
)

pre_word_count = count_words(pre_test_text)
st.caption(f"Word count: {pre_word_count}")

if st.button("Generate AI feedback"):
    if not participant_id.strip():
        st.error("Please enter your participant ID before continuing.")
    elif pre_word_count < 100:
        st.error("Your text is too short. Please write a longer text before requesting feedback.")
    else:
        with st.spinner("Generating feedback..."):
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
    st.header("AI Feedback")
    st.text(st.session_state.feedback)

    st.divider()
    st.header("Task 2")
    st.write(
        """
        Schrijf nu een NIEUWE tekst van ongeveer 150-200 woorden in het Nederlands.

        Onderwerp: Is online onderwijs goed voor studenten?

        Geef je mening en leg uit waarom.
        """
    )

    post_test_text = st.text_area(
        "Write your second text here",
        height=250
    )

    post_word_count = count_words(post_test_text)
    st.caption(f"Word count: {post_word_count}")

    if st.button("Submit experiment"):
        if post_word_count < 100:
            st.error("Your second text is too short. Please write a longer text before submitting.")
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
            st.success("Experiment completed. Please return to the questionnaire.")


if st.session_state.completed:
    st.balloons()
