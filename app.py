import streamlit as st
import pandas as pd
import re
import pdfplumber
from io import BytesIO

# --- Extract text from PDF ---
def extract_text_from_pdf(file):
    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text

# --- Parse details from text ---
def parse_loan_details(text):
    details = {
        "Customer Name": None,
        "Customer Mobile": None,
        "Guarantor Name": None,
        "Guarantor Mobile": None,
        "Loan No": None,
        "Loan Date": None,
        "Loan Amount": None,
        "Loan Interest": None,
        "Agreement Value": None,
        "Tenure in Months": None,
        "1st Installment Date": None,
        "Last Installment Date": None,
        "Receipt Amount": None,
        "Arrears Amount": None,
        "Settlement Total": None
    }

    # --- Customer ---
    cust_name = re.search(r"CUSTOMER DETAILS.*?Name\s*:(.+)", text, re.S)
    if cust_name:
        details["Customer Name"] = cust_name.group(1).split("\n")[0].strip()

    cust_mobile = re.search(r"Mobile No:\s*([0-9]{6,})", text)
    if cust_mobile:
        details["Customer Mobile"] = cust_mobile.group(1)

    # --- Guarantor ---
    guar_name = re.search(r"GUARANTOR DETAILS.*?Name\s*:(.+)", text, re.S)
    if guar_name:
        details["Guarantor Name"] = guar_name.group(1).split("\n")[0].strip()

    mobiles = re.findall(r"Mobile No:([0-9]{6,})", text)
    if len(mobiles) > 1:
        details["Guarantor Mobile"] = mobiles[1]

    # --- Loan summary (fixed regex) ---
    loan = re.search(
        r"(UTNGR\d+)\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2})\s+([\d,]+\.\d{2})\s+(\d+)\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})",
        text
    )
    if loan:
        details["Loan No"] = loan.group(1)
        details["Loan Date"] = loan.group(2)
        details["Loan Amount"] = float(loan.group(3).replace(",", ""))
        details["Loan Interest"] = float(loan.group(4).replace(",", ""))
        details["Tenure in Months"] = int(loan.group(5))
        details["1st Installment Date"] = loan.group(6)
        details["Last Installment Date"] = loan.group(7)
        details["Agreement Value"] = details["Loan Amount"] + details["Loan Interest"]

    # --- Receipt Amount ---
    receipts = re.findall(r"Receipt On Account.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)
    if receipts:
        total = sum([float(r.replace(",", "")) for r in receipts])
        details["Receipt Amount"] = total

    # --- Arrears ---
    arrears = re.findall(r"Arrears As On.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)
    if arrears:
        details["Arrears Amount"] = float(arrears[-1].replace(",", ""))

    # --- Settlement ---
    settlement = re.findall(r"Settlement.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)
    if settlement:
        details["Settlement Total"] = float(settlement[-1].replace(",", ""))

    return details

# --- Streamlit UI ---
st.title("📑 Loan SOA PDF Extractor → Fixed Regex Version")

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for uploaded_file in uploaded_files:
        text = extract_text_from_pdf(uploaded_file)
        details = parse_loan_details(text)
        data.append(details)

    df = pd.DataFrame(data)
    st.dataframe(df)

    # Excel download
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="loan_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
