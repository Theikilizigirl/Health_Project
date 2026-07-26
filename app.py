import hashlib
import hmac
import re
import secrets

import streamlit as st
from supabase import create_client


# Page configuration
st.set_page_config(
    page_title="Digital Health Information Study",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    color: #1f77b4;
    text-align: center;
    font-weight: bold;
    margin-bottom: 0.3rem;
}
.sub-header {
    font-size: 1.15rem;
    text-align: center;
    color: #555555;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)


# Database and Microsoft Forms

TABLE_NAME = "Health Project Framing"

positive_form = "https://forms.cloud.microsoft/r/g5cLZzVvq9?origin=lprLink"
negative_form = "https://forms.cloud.microsoft/r/f42CQ5tWAZ?origin=lprLink"
neutral_form = "https://forms.cloud.microsoft/r/f42CQ5tWAZ?origin=lprLink"

form_links = {
    "Positive": positive_form,
    "Negative": negative_form,
    "Neutral": neutral_form
}


# Database connection

@st.cache_resource(show_spinner=False)
def connect_to_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["service_role_key"]
    )


# Email and participant assignment functions

def normalise_email(email):
    return email.strip().lower()


def validate_email(email):
    email_pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    return bool(re.fullmatch(email_pattern, normalise_email(email)))


def create_email_hash(email):
    private_key = st.secrets["security"]["email_hash_key"].encode("utf-8")
    normalised_email = normalise_email(email).encode("utf-8")
    return hmac.new(private_key, normalised_email, hashlib.sha256).hexdigest()


def generate_participant_code():
    characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    random_part = "".join(secrets.choice(characters) for _ in range(8))
    return f"DH-{random_part}"


def get_assignment_by_code(participant_code):
    supabase = connect_to_supabase()

    response = (
        supabase.table(TABLE_NAME)
        .select("participant_code, assigned_condition, status")
        .eq("participant_code", participant_code.strip().upper())
        .limit(1)
        .execute()
    )

    return response.data[0] if response.data else None


def create_or_retrieve_assignment(email):
    supabase = connect_to_supabase()
    email_hash = create_email_hash(email)

    for _ in range(10):
        participant_code = generate_participant_code()

        try:
            response = supabase.rpc(
                "assign_health_project_participant",
                {"p_code": participant_code, "p_email_hash": email_hash}
            ).execute()

            if response.data:
                record = response.data[0]

                return {
                    "participant_code": record["participant_code"],
                    "assigned_condition": record["assigned_condition"],
                    "status": record["assignment_status"],
                    "was_existing": record["was_existing"]
                }

        except Exception as error:
            error_message = str(error).lower()

            if "participant_code" in error_message or "duplicate key" in error_message:
                continue

            raise error

    raise RuntimeError("A unique survey assignment could not be generated.")


def save_assignment_to_session(assignment):
    st.session_state.participant_code = assignment["participant_code"]
    st.session_state.assigned_condition = assignment["assigned_condition"]
    st.session_state.assignment_status = assignment["status"]
    st.session_state.was_existing = assignment.get("was_existing", False)


def remove_invalid_assignment_parameter():
    try:
        del st.query_params["assignment"]
    except Exception:
        pass


def restore_assignment_from_url():
    assignment_code = st.query_params.get("assignment", "")

    if not assignment_code:
        return False

    try:
        assignment = get_assignment_by_code(assignment_code)
    except Exception:
        remove_invalid_assignment_parameter()
        return False

    if not assignment:
        remove_invalid_assignment_parameter()
        return False

    save_assignment_to_session({
        "participant_code": assignment["participant_code"],
        "assigned_condition": assignment["assigned_condition"],
        "status": assignment["status"],
        "was_existing": True
    })

    return True


# Assigned questionnaire page
def display_assigned_survey():
    assigned_condition = st.session_state.assigned_condition
    assignment_status = st.session_state.get("assignment_status", "assigned")
    was_existing = st.session_state.get("was_existing", False)

    if assignment_status == "completed":
        st.success("This email address has already been used to complete the study. Thank you for taking part.")
        return

    if assignment_status == "excluded":
        st.warning("This questionnaire assignment is currently unavailable. Please contact the researcher for assistance.")
        return

    assigned_form = form_links.get(assigned_condition)

    if not assigned_form:
        st.error("The assigned questionnaire could not be found. Please contact the researcher.")
        return

    if was_existing:
        st.info("A questionnaire was previously assigned to this email address. Your original questionnaire has been restored.")
    else:
        st.success("Your questionnaire has been assigned successfully.")

    st.write(
        "Please select the button below to open your assigned questionnaire. "
        "Complete and submit the questionnaire only once."
    )

    st.link_button(
        "Open My Assigned Questionnaire",
        assigned_form,
        type="primary",
        use_container_width=True
    )

    st.caption(
        "Opening the questionnaire does not automatically submit your response. "
        "You must complete the Microsoft Form and select Submit."
    )


# Restore an existing browser assignment

if "participant_code" not in st.session_state:
    restore_assignment_from_url()


# Page heading

st.markdown(
    '<div class="main-header">Digital Health Information Study</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-header">Understanding how people respond to information '
    'provided by digital health services</div>',
    unsafe_allow_html=True
)


# Show the assigned questionnaire if an assignment already exists
if "participant_code" in st.session_state:
    display_assigned_survey()
    st.stop()


# Participant Information Sheet
st.info(
    "Thank you for your interest in this research. "
    "Please read the Participant Information Sheet before continuing."
)

with st.expander("Participant Information Sheet: Please click to open and read"):
    st.markdown("""
### What is the purpose of the study?

This study examines how people interpret information provided by digital health services and how this information affects their views about using such services. You will be shown a short scenario about a digital health portal and asked to provide your views about it.

### Why have I been invited to take part?

You may take part if:

- You are aged 18 years or above.
- You can read and understand English.
- You are capable of making your own decisions.
- You have experience using at least one digital service, such as social media, a health application or online banking.
- You have internet access to complete the questionnaire.

### Do I have to take part?

Participation is voluntary. You are under no obligation to take part and will not experience any penalty or loss of benefit if you choose not to participate. You may leave the study at any time before submitting your questionnaire response.

### What will I have to do?

You will read a short scenario about a digital health portal and answer questions about your views of the portal and your willingness to share personal health data. You will also answer a small number of demographic questions. The questionnaire should take approximately 10 minutes and should only be completed once.
""")

    st.info(
        "There are no right or wrong answers. Please answer each question "
        "honestly based on your own views and reactions to the scenario."
    )

    st.markdown("""
### Email privacy and confidentiality

Your email address is requested only to prevent duplicate questionnaire assignments and to restore your original questionnaire if you refresh or return to the application. It is converted into a secure coded identifier before being processed.

Your actual email address is not stored in the study database, passed to Microsoft Forms or connected to your questionnaire responses. Your name and actual medical information will not be requested.

The questionnaire responses will be stored securely and accessed only by the researcher and authorised members of the research team.

### Contact for further information

**Researcher:** shekinah.ikilizi@northumbria.ac.uk  
**Supervisor:** m.cholerzynski@northumbria.ac.uk
""")


# Eligibility, email and consent form

st.divider()

with st.form("participant_access_form", clear_on_submit=False):
    st.markdown("### Eligibility confirmation")

    eligibility = st.checkbox(
        "I confirm that I am aged 18 years or above, can read and understand "
        "English, and meet the participation criteria listed in the "
        "Participant Information Sheet."
    )

    st.markdown("### Email address")

    participant_email = st.text_input(
        "Enter your email address",
        placeholder="example@email.com",
        help="Used only to prevent duplicate assignments and restore your original questionnaire."
    )

    st.markdown("### Informed consent")

    consent = st.checkbox(
        "I confirm that I have read and understood the Participant Information "
        "Sheet. I understand that participation is voluntary, that I may leave "
        "before submitting my response, and I agree to take part in this study."
    )

    submitted = st.form_submit_button(
        "Continue to My Questionnaire",
        type="primary",
        use_container_width=True
    )


# Form validation and questionnaire allocation

if submitted:
    if not eligibility:
        st.error("Please confirm that you meet the eligibility criteria.")

    elif not validate_email(participant_email):
        st.error("Please enter a valid email address.")

    elif not consent:
        st.error("Please provide informed consent before continuing.")

    else:
        try:
            with st.spinner("Preparing your questionnaire..."):
                assignment = create_or_retrieve_assignment(participant_email)

            save_assignment_to_session(assignment)
            st.query_params["assignment"] = assignment["participant_code"]
            st.rerun()

        except Exception:
            st.error(
                "Your questionnaire could not be assigned. Please refresh the "
                "page and try again. If the problem continues, contact the researcher."
            )
