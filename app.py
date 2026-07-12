import streamlit as st
import time

# Set page configuration for a better layout
st.set_page_config(
    page_title="Digital Health Portal Study",
    page_icon="🩺",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS to make the header text look beautiful
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        font-weight: bold;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #555555;
        margin-bottom: 2rem;
    }
    </style>
""", unsafe_allow_html=True)

# Main Titles
st.markdown('<div class="main-header">Digital Health Portal Study</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Investigating Privacy Disclosure Framing and Trust Management</div>', unsafe_allow_html=True)

st.info("Thank you for your interest in this research. Please read the Participant Information Sheet below before proceeding to the survey.")

# Participant Information Sheet hidden inside an expander to keep the UI clean
with st.expander("Participant Information Sheet (Please click to open and read)", expanded=False):
    st.markdown("### What is the purpose of the study?")
    st.write("This study is looking at how the way information is presented to you affects how comfortable you feel disclosing your personal health data online. You will be shown a short scenario about a digital health portal and asked to share your thoughts and feelings about it. The study aims to understand whether the wording used in privacy notices influences how much people trust a service and how willing they are to share their information.")
    
    st.markdown("### Why have I been invited to take part?")
    st.write("You have been invited to take part as you meet the following criteria:")
    st.markdown("""
    * You are an adult aged 18+ years
    * Able to read and understand English
    * Capable of making your own decisions
    * Have experience using at least one digital service (e.g., social media, a health app, or an online banking app)
    * Have access to the internet to complete an online survey
    """)
    
    st.markdown("### Do I have to take part?")
    st.write("You are under no obligation to take part and you will not experience any loss of benefit or penalty if you choose not to participate.")
    
    st.markdown("### What will I have to do?")
    st.write("You will be asked to complete a short online survey that consists of four parts. First, you will answer a few questions about yourself, such as your age, gender, and education level. You will then be shown a short written scenario about a digital health portal and asked to read it carefully. After reading the scenario, you will rate statements about your feelings toward the portal and your willingness to share personal health information. The survey should take no longer than 10 to 15 minutes to complete and will only need to be done once. There are no right or wrong answers; we are simply interested in your honest thoughts and feelings.")

    st.markdown("### Confidentiality and Data Storage")
    st.write("You will be allocated a unique participant code that will be used to identify any data that you provide. Your name and other personal details will not be associated with your data. All data will be stored on the University's secure network and will be treated in accordance with the Data Protection Act.")

    st.markdown("### Contact for further information:")
    st.write("**Researcher:** shekinah.ikilizi@northumbria.ac.uk")
    st.write("**Supervisor:** m.cholerzynski@northumbria.ac.uk")

st.divider()

# Consent Checkbox
st.markdown("### Informed Consent")
st.write("Please confirm your consent to participate by checking the box below:")
consent = st.checkbox("I have carefully read and understood the Participant Information Sheet. I understand I am free to withdraw from the study at any time, and I agree to take part in this study.")

# Microsoft Form Links
positive_form = "https://forms.office.com/e/ZGdebwL9g7?origin=lprLink"
negative_form = "https://forms.office.com/e/ZNjKt7Ww24?origin=lprLink"
neutral_form = "https://forms.office.com/e/PJtM9MEEzU?origin=lprLink"
form_links = [positive_form, negative_form, neutral_form]

# Cloud-Safe Time-Based Assignment
if 'assigned_link' not in st.session_state:
    # Grab the current time in milliseconds
    current_time_ms = int(time.time() * 1000)
    
    # Use modulo 3 to divide the milliseconds evenly into 0, 1, or 2
    form_index = current_time_ms % 3
    
    # Assign the link and save it to the user's session
    st.session_state.assigned_link = form_links[form_index]

st.divider()

# Only show the survey button if the user has consented
if consent:
    st.success("Thank you for your consent. Please click the button below to proceed to the survey. The survey will open in a new tab.")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.link_button("Start Survey", st.session_state.assigned_link, use_container_width=True)
else:
    st.warning("You must check the consent box above to unlock the survey link.")
