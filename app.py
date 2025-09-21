import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader
from io import BytesIO

st.title("📑 Loan Details Extractor (Final Fixed)")

def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        if page.extract_text():
            text += page.extract_text() + "\n"
    return text

def extract_details_from_pdf(uploaded_file):
    text = extract_text_from_pdf(uploaded_file)

    def find(pattern):
        m = re.search(pattern, text, re.I)
        return m.group(1).strip() if m else ""

    # Customer
    cust_name = find(r"Customer Name\s*:\s*([A-Z ]+)")
    cust_mobile = find(r"Customer Mobile\s*:\s*(\d{10})")
    cust_addr = find(r"Customer Address\s*:\s*(.+)")

    # Guarantor
    guar_name = find(r"Guarantor Name\s*:\s*([A-Z ]+)")
    guar_mobile = find(r"Guarantor Mobile\s*:\s*(\d{10})")
    guar_addr = find(r"Guarantor Address\s*:\s*(.+)")

    # Loan info
    branch = find(r"Branch\s*:\s*(\w+)")
    loan_no = find(r"Loan No\s*:\s*(\S+)")
    loan_date = find(r"Loan Date\s*:\s*(\d{2}/\d{2}/\d{4})")

    loan_month, loan_year = "", ""
    if loan_date:
        parts = loan_date.split("/")
        if len(parts) == 3:
            month_map = {
                "01": "JAN","02": "FEB","03": "MAR","04": "APR",
                "05": "MAY","06": "JUN","07": "JUL","08": "AUG",
                "09": "SEP","10": "OCT","11": "NOV","12": "DEC"
            }
            loan_month = month_map.get(parts[1], parts[1])
            loan_year = parts[2]

    loan_amt = find(r"Loan Amount\s*:\s*([\d,]+\.?\d*)").replace(",", "")
    int_amt = find(r"Loan Interest\s*:\s*([\d,]+\.?\d*)").replace(",", "")
    agree_val = find(r"Agreement Value\s*:\s*([\d,]+\.?\d*)").replace(",", "")
    tenure = find(r"Tenure\s*:\s*(\d+)")
    inst_start = find(r"Installment Start\s*:\s*(\d{2}/\d{2}/\d{4})")
    inst_end = find(r"Installment End\s*:\s*(\d{2}/\d{2}/\d{4})")

    # Amounts
    receipt_amt = find(r"Receipt Amount\s*:\s*([\d,]+\.?\d*)").replace(",", "")
    arrears_amt = find(r"Arrears Amount\s*:\s*([\d,]+\.?\d*)").replace(",", "")
    settle_total = find(r"Settlement Total\s*:\s*([\d,]+\.?\d*)").replace(",", "")

    return {
        "Customer Name": cust_name,
        "Customer Address": cust_addr,
        "Customer Mobile": cust_mobile,
        "Guarantor Name": guar_name,
        "Guarantor Address": guar_addr,
        "Guarantor Mobile": guar_mobile,
        "Branch": branch,
        "Loan No": loan_no,
        "Loan Date": loan_date,
        "Loan Month": loan_month,
        "Loan Year": loan_year,
        "Loan Amount": loan_amt,
        "Loan Interest": int_amt,
        "Agreement Value": agree_val,
        "Tenure in Months": tenure,
        "Installment Start": inst_start,
        "Installment End": inst_end,
        "Receipt Amount": receipt_amt,
        "Arrears Amount": arrears_amt,
        "Settlement Total": settle_total
    }

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
