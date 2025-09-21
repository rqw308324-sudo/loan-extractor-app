
import streamlit as st
import pdfplumber
import pandas as pd
import re
from io import BytesIO

st.title("Loan PDF Extractor (Bug-fixed)")

def extract_details_from_pdf(file):
    data = {
        "Customer Name": "NOT FOUND",
        "Customer Address": "NOT FOUND",
        "Customer Mobile": "NOT FOUND",
        "Guarantor Name": "NOT FOUND",
        "Guarantor Address": "NOT FOUND",
        "Guarantor Mobile": "NOT FOUND",
        "Branch": "NOT FOUND",
        "Loan No": "NOT FOUND",
        "Loan Date": "NOT FOUND",
        "Loan Month": "NOT FOUND",
        "Loan Year": "NOT FOUND",
        "Loan Amount": "NOT FOUND",
        "Plan Interest": "NOT FOUND",
        "Agreement Value": "NOT FOUND",
        "Tenure in Months": "NOT FOUND",
        "Installment Start": "NOT FOUND",
        "Installment End": "NOT FOUND",
        "Receipt Amount": "NOT FOUND",
        "Arrears Amount": "NOT FOUND",
        "Settlement Total": "NOT FOUND"
    }

    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # Debug log
    st.text_area("Extracted Text Preview", text[:2000], height=200)

    # Regex patterns
    patterns = {
        "Customer Name": r"Customer Name\s*:\s*(.*)",
        "Customer Address": r"Customer Address\s*:\s*(.*)",
        "Customer Mobile": r"Customer Mobile\s*:\s*(\d+)",
        "Guarantor Name": r"Guarantor Name\s*:\s*(.*)",
        "Guarantor Address": r"Guarantor Address\s*:\s*(.*)",
        "Guarantor Mobile": r"Guarantor Mobile\s*:\s*(\d+)",
        "Branch": r"Branch\s*:\s*(\w+)",
        "Loan No": r"Loan No\s*:\s*(\w+)",
        "Loan Date": r"(\d{2}/\d{2}/\d{4})",
        "Loan Amount": r"Loan Amount\s*:\s*(\d+[,.]?\d*)",
        "Plan Interest": r"Interest\s*:?\s*(\d+[,.]?\d*)",
        "Agreement Value": r"Agreement Value\s*:?\s*(\d+[,.]?\d*)",
        "Tenure in Months": r"(\d+)\s*Months",
        "Installment Start": r"Installment Start\s*:?\s*(\d{2}/\d{2}/\d{4})",
        "Installment End": r"Installment End\s*:?\s*(\d{2}/\d{2}/\d{4})",
        "Receipt Amount": r"Receipt Amount\s*:?\s*(\d+[,.]?\d*)",
        "Arrears Amount": r"Arrears Amount\s*:?\s*(\d+[,.]?\d*)",
        "Settlement Total": r"Settlement Total\s*:?\s*(\d+[,.]?\d*)"
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            data[key] = match.group(1).strip()

    # Loan Month & Year
    if data["Loan Date"] != "NOT FOUND":
        try:
            day, month, year = data["Loan Date"].split("/")
            months = ["JAN","FEB","MAR","APR","MAY","JUN","JUL","AUG","SEP","OCT","NOV","DEC"]
            data["Loan Month"] = months[int(month)-1]
            data["Loan Year"] = year
        except:
            pass

    return data

uploaded_files = st.file_uploader("Upload Loan PDF(s)", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        details = extract_details_from_pdf(file)
        all_data.append(details)

    df = pd.DataFrame(all_data)

    st.dataframe(df)

    # Safe Excel download
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Loans")
    st.download_button("Download Excel", output.getvalue(), file_name="loan_details.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
