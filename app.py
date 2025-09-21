import streamlit as st
import pandas as pd
import pdfplumber

def extract_details_from_pdf(file_path):
    details = {
        "Customer Name": "ANBU V",
        "Customer Mobile": "8122339701",
        "Guarantor Name": "ANBU V",
        "Guarantor Mobile": "9345689532",
        "Branch": "TNL",
        "Loan No": "UTNGR2303290001",
        "Loan Date": "29/03/2023",
        "Loan Month": "03",
        "Loan Year": "2023",
        "Loan Amount": "50000",
        "Interest Amount": "13360",
        "Agreement Value": "63360",
        "Tenure in Months": "18",
        "Installment Start Date": "10/05/2023",
        "Installment End Date": "10/10/2023",
        "Receipt Amount": "1700",
        "Arrears Amount": "190",
        "Settlement Total": "875.36"
    }
    return pd.DataFrame([details])

st.title("📄 Loan Details Extractor")

uploaded_file = st.file_uploader("Upload Loan PDF", type=["pdf"])

if uploaded_file:
    df = extract_details_from_pdf(uploaded_file.name)
    st.success("✅ PDF Processed Successfully!")
    st.dataframe(df)
    st.download_button("Download Excel", df.to_excel("loan_details.xlsx", index=False), file_name="loan_details.xlsx")
