import streamlit as st
import pandas as pd
from model import draft_reply   # import AI reply function

st.title("AI Email Assistant")

uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)

    st.subheader("Uploaded Emails")
    st.dataframe(df)

    # Button to generate replies
    if st.button("Generate AI Replies"):
        df["AI Reply"] = df.apply(
            lambda row: draft_reply(row["subject"], row["body"]), axis=1
        )
        st.success("Replies generated!")
        st.dataframe(df[["sender", "subject", "AI Reply"]])

        # Save CSV with replies
        df.to_csv("processed_emails.csv", index=False)
        st.download_button(
            label="Download processed_emails.csv",
            data=open("processed_emails.csv", "rb").read(),
            file_name="processed_emails.csv",
            mime="text/csv"
        )
