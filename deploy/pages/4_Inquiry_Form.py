import streamlit as st

st.set_page_config(page_title="📝 Submit Inquiry", layout="wide")
st.title("📨 Inquiry Submission")

with st.form("inquiry_form"):
    st.subheader("Contact Information")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name", placeholder="Bola Tinubu")
    with col2:
        phone = st.text_input("Phone Number", placeholder="+1 234 567 8900")

    email = st.text_input("Email", placeholder="bola@example.com")
    st.subheader("Message")
    message = st.text_area("Describe your inquiry")

    submitted = st.form_submit_button("📬 Submit Inquiry")
    if submitted:
        if not name or not email or not message:
            st.warning("Please fill out all required fields.")
        else:
            st.success("✅ Your inquiry has been submitted!")
            st.info(f"Thank you {name}, we’ll contact you at {email}.")
