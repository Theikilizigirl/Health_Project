import hashlib
import hmac
import re
import secrets
import streamlit as st
from supabase import create_client

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

TABLE_NAME = "Health Project Framing"

# Microsoft Form Links
positive_form = "https://forms.office.com/e/ZGdebwL9g7?origin=lprLink"
negative_form = "https://forms.office.com/e/ZNjKt7Ww24?origin=lprLink"
neutral_form = "https://forms.office.com/e/PJtM9MEEzU?origin=lprLink"

form_links = {
    "Positive": positive_form,
    "Negative": negative_form,
    "Neutral": neutral_form
}

@st.cache_resource
def connect_to_supabase():
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["service_role_key"]
    )

try:
    supabase = connect_to_supabase()
except Exception:
    st.error(
        "The study database could not be connected. "
        "Please contact the researcher or try again later."
    )
    st.stop()

def normalise_email(email):
    return email.strip().lower()

def validate_email(email):
    email = normalise_email(email)
    pattern = r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+$"
    return bool(re.fullmatch(pattern, email))

def create_email_hash(email):
    normalised_email = normalise_email(email)
    private_key = st.secrets["security"]["email_hash_key"].encode("utf-8")

    return hmac.new(
        private_key,
        normalised_email.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def generate_participant_code():
    characters = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    random_part = "".join(
        secrets.choice(characters)
        for _ in range(8)
    )
    return f"DH-{random_part}"

def get_assignment_by_code(participant_code):
    response = (
        supabase.table(TABLE_NAME)
        .select("participant_code, assigned_condition, status")
        .eq("participant_code", participant_code.strip().upper())
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None

def create_or_retrieve_assignment(email):
    email_hash = create_email_hash(email)

    for _ in range(10):
        participant_code = generate_participant_code()

        try:
            response = supabase.rpc(
                "assign_health_project_participant",
                {
                    "p_code": participant_code,
                    "p_email_hash": email_hash
                }
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

            if (
                "participant_code" in error_message
                or "duplicate key" in error_message
            ):
                continue

            raise error

    raise RuntimeError(
        "A unique survey assignment could not be generated."
    )

def save_assignment_to_session(assignment):
    st.session_state.participant_code = assignment["participant_code"]
    st.session_state.assigned_condition = assignment["assigned_condition"]
    st.session_state.assignment_status = assignment["status"]
    st.session_state.was_existing = assignment.get("was_existing", False)

def restore_assignment_from_url():
    assignment_code = st.query_params.get("assignment", "")

    if not assignment_code:
        return False

    try:
        assignment = get_assignment_by_code(assignment_code)
    except Exception:
        return False

    if not assignment:
        try:
            del st.query_params["assignment"]
        except Exception:
            pass

        return False

    save_assignment_to_session({
        "participant_code": assignment["participant_code"],
        "assigned_condition": assignment["assigned_condition"],
        "status": assignment["status"],
        "was_existing": True
    })

    return True

def display_assigned_survey():
    assigned_condition = st.session_state.assigned_condition
    assignment_status = st.session_state.get(
        "assignment_status",
        "assigned"
    )
    was_existing = st.session_state.get(
        "was_existing",
        False
    )

    if assignment_status == "completed":
        st.success(
            "This email address has already been used to complete the study. "
            "Thank you for taking part."
        )
        return

    if assignment_status == "excluded":
        st.warning(
            "This survey assignment is currently unavailable. "
            "Please contact the researcher for assistance."
        )
        return

    assigned_form = form_links.get(assigned_condition)

    if not assigned_form:
        st.error(
            "The assigned survey could not be found. "
            "Please contact the researcher."
        )
        return

    if was_existing:
        st.info(
            "A survey was previously assigned to this email address. "
            "Your original assigned survey has been restored."
        )
    else:
        st.success(
            "Your survey has been assigned successfully."
        )

    st.write(
        "Please use the button below to open your assigned questionnaire. "
        "Complete and submit the questionnaire only once."
    )

    st.link_button(
        "Open My Assigned Survey",
        assigned_form,
        type="primary",
        use_container_width=True
    )

    st.caption(
        "Opening the questionnaire does not automatically submit a response. "
        "You must complete the Microsoft Form and select Submit."
    )

if "participant_code" not in st.session_state:
    restore_assignment_from_url()

st.markdown(
    '<div class="main-header">Digital Health Information Study</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="sub-header">'
    'Understanding how people respond to information provided by '
    'digital health services'
    '</div>',
    unsafe_allow_html=True
)

if "participant_code" in st.session_state:
    display_assigned_survey()
    st.stop()

st.info(
    "Thank you for your interest in this research. "
    "Please read the Participant Information Sheet before continuing."
)

with st.expander(
    "Participant Information Sheet: Please click to open and read",
    expanded=False
):
    st.markdown("### What is the purpose of the study?")

    st.write(
        "This study examines how people interpret information provided "
        "by digital health services and how this information affects "
        "their views about using such services. You will be shown a "
        "short scenario about a digital health portal and asked to "
        "provide your views about it."
    )

    st.markdown("### Why have I been invited to take part?")

    st.write(
        "You may take part if you meet all the following criteria:"
    )

    st.markdown("""
- You are aged 18 years or above.
- You can read and understand English.
- You are capable of making your own decisions.
- You have experience using at least one digital service, such as social media, a health application or online banking.
- You have internet access to complete the survey.
""")

    st.markdown("### Do I have to take part?")

    st.write(
        "Participation is voluntary. You are under no obligation to "
        "take part and will not experience any penalty or loss of "
        "benefit if you choose not to participate. You may stop "
        "completing the study at any point before submitting your "
        "questionnaire response."
    )

    st.markdown("### What will I have to do?")

    st.write(
        "You will read a short scenario about a digital health portal "
        "and answer questions about your views of the portal and your "
        "willingness to share personal health data. You will also "
        "answer a small number of demographic questions. The questionnaire "
        "should take approximately 10 to 15 minutes and should only "
        "be completed once."
    )

    st.markdown("### Why is my email address requested?")

    st.write(
        "Your email address is used only to prevent duplicate survey "
        "assignments and to restore your original assigned questionnaire "
        "if you refresh or return to this page. The email address is "
        "converted into a secure coded identifier before being stored. "
        "Your actual email address is not saved in the study database "
        "or connected to your Microsoft Form responses."
    )

    st.markdown("### Confidentiality and data storage")

    st.write(
        "Your name will not be requested. Your survey assignment record "
        "and Microsoft Form responses will be stored separately. Research "
        "data will be stored securely and handled in accordance with "
        "relevant data-protection requirements and Northumbria University "
        "research policies."
    )

    st.markdown("### Contact for further information")

    st.write(
        "**Researcher:** shekinah.ikilizi@northumbria.ac.uk"
    )

    st.write(
        "**Supervisor:** m.cholerzynski@northumbria.ac.uk"
    )

st.divider()

with st.form("participant_access_form"):
    st.markdown("### Eligibility")

    eligibility = st.checkbox(
        "I confirm that I am aged 18 years or above, can understand "
        "English, and meet the participation criteria listed above."
    )

    st.markdown("### Email address")

    participant_email = st.text_input(
        "Enter your email address",
        placeholder="example@email.com",
        help=(
            "Your email is converted into a secure identifier. "
            "The actual email address is not stored."
        )
    )

    st.markdown("### Informed consent")

    consent = st.checkbox(
        "I confirm that I have read and understood the Participant "
        "Information Sheet. I understand that participation is "
        "voluntary, and I agree to take part in this study."
    )

    submitted = st.form_submit_button(
        "Continue to My Survey",
        type="primary",
        use_container_width=True
    )

if submitted:
    if not eligibility:
        st.error(
            "You must confirm that you meet the eligibility criteria."
        )

    elif not validate_email(participant_email):
        st.error(
            "Please enter a valid email address."
        )

    elif not consent:
        st.error(
            "You must provide informed consent before continuing."
        )

    else:
        try:
            with st.spinner(
                "Creating or retrieving your survey assignment..."
            ):
                assignment = create_or_retrieve_assignment(
                    participant_email
                )

            save_assignment_to_session(assignment)

            st.query_params["assignment"] = assignment["participant_code"]

            st.rerun()

        except Exception:
            st.error(
                "Your survey could not be assigned. Please refresh "
                "the page and try again. If the problem continues, "
                "contact the researcher."
            )
