import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader
from io import BytesIO

st.title("📑 Loan Details Extractor (Bug-fixed)")

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def extract_details_from_pdf(uploaded_file):
    text = extract_text_from_pdf(uploaded_file)

    def find(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else ""

    details = {
        "Customer Name": find(r"Customer Name\s*:\s*(.+)"),
        "Customer Address": find(r"Customer Address\s*:\s*(.+)"),
        "Customer Mobile": find(r"Customer Mobile\s*:\s*(\d{10})"),
        "Guarantor Name": find(r"Guarantor Name\s*:\s*(.+)"),
        "Guarantor Mobile": find(r"Guarantor Mobile\s*:\s*(\d{10})"),
        "Branch": find(r"Branch\s*:\s*(\w+)"),
        "Loan No": find(r"Loan No\s*:\s*(\S+)"),
        "Loan Date": find(r"Loan Date\s*:\s*(\d{2}/\d{2}/\d{4})"),
        "Loan Amount": find(r"Loan Amount\s*:\s*([\d,]+\.?\d*)").replace(",", ""),
        "Loan Interest": find(r"Loan Interest\s*:\s*([\d,]+\.?\d*)").replace(",", ""),
        "Agreement Value": find(r"Agreement Value\s*:\s*([\d,]+\.?\d*)").replace(",", ""),
        "Tenure in Months": find(r"Tenure\s*:\s*(\d+)"),
        "Installment Start": find(r"Installment Start\s*:\s*(\d{2}/\d{2}/\d{4})"),
        "Installment End": find(r"Installment End\s*:\s*(\d{2}/\d{2}/\d{4})"),
        "Receipt Amount": find(r"Receipt Amount\s*:\s*([\d,]+\.?\d*)").replace(",", ""),
        "Arrears Amount": find(r"Arrears Amount\s*:\s*([\d,]+\.?\d*)").replace(",", ""),
        "Settlement Total": find(r"Settlement Total\s*:\s*([\d,]+\.?\d*)").replace(",", ""),
    }

    # Loan Month & Year split
    if details["Loan Date"]:
        parts = details["Loan Date"].split("/")
        if len(parts) == 3:
            month_map = {
                "01": "JAN","02": "FEB","03": "MAR","04": "APR",
                "05": "MAY","06": "JUN","07": "JUL","08": "AUG",
                "09": "SEP","10": "OCT","11": "NOV","12": "DEC"
            }
            details["Loan Month"] = month_map.get(parts[1], parts[1])
            details["Loan Year"] = parts[2]
        else:
            details["Loan Month"], details["Loan Year"] = "", ""
    else:
        details["Loan Month"], details["Loan Year"] = "", ""

    return details

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    rows = [extract_details_from_pdf(f) for f in uploaded_files]
    df = pd.DataFrame(rows)
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Loans")
    st.download_button(
        "📥 Download Excel",
        data=output.getvalue(),
        file_name="loan_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
