import streamlit as st
import pandas as pd
import re
from PyPDF2 import PdfReader
from io import BytesIO

# --- Extract text from PDF ---
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

# --- Parse details (basic) ---
def parse_loan_details(text):
    details = {
        "Customer Name": None,
        "Customer Address": None,
        "Customer Mobile": None,
        "Guarantor Name": None,
        "Guarantor Address": None,
        "Guarantor Mobile": None,
        "Loan No": None,
        "Loan Date": None,
        "Loan Month": None,
        "Loan Year": None,
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

    # Customer name
    m = re.search(r"CUSTOMER DETAILS.*?Name\s*:([^\n\r]+)", text, re.S)
    if m:
        details["Customer Name"] = m.group(1).strip()

    mobiles = re.findall(r"Mobile No[:\s]*([0-9]{6,})", text)
    if mobiles:
        details["Customer Mobile"] = mobiles[0]
        if len(mobiles) > 1:
            details["Guarantor Mobile"] = mobiles[1]

    # Guarantor name
    gm = re.search(r"GUARANTOR DETAILS.*?Name\s*:([^\n\r]+)", text, re.S)
    if gm:
        details["Guarantor Name"] = gm.group(1).strip()

    # Loan info
    loan = re.search(r"(UTNGR\d{9,})\s+(\d{2}/\d{2}/\d{4})\s+([\d,]+\.\d{2}|\d+)\s+([\d,]+\.\d{2}|\d+)\s+(\d{1,3})\s+(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})", text)
    if loan:
        details["Loan No"] = loan.group(1).strip()
        details["Loan Date"] = loan.group(2).strip()
        la = loan.group(3).replace(",", "")
        li = loan.group(4).replace(",", "")
        details["Loan Amount"] = float(la)
        details["Loan Interest"] = float(li)
        details["Tenure in Months"] = int(loan.group(5))
        details["1st Installment Date"] = loan.group(6)
        details["Last Installment Date"] = loan.group(7)
        details["Agreement Value"] = details["Loan Amount"] + details["Loan Interest"]
        dparts = details["Loan Date"].split("/")
        if len(dparts) == 3:
            details["Loan Month"] = dparts[1]
            details["Loan Year"] = dparts[2]

    # Receipt amount
    receipts = re.findall(r"Receipt On Account.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
    if receipts:
        total = sum([float(r.replace(",", "")) for r in receipts])
        details["Receipt Amount"] = total

    # Arrears
    arrears = re.findall(r"Arrears As On.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
    if arrears:
        details["Arrears Amount"] = float(arrears[-1].replace(",", ""))

    # Settlement
    settlement = re.findall(r"Settlement.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)", text)
    if settlement:
        details["Settlement Total"] = float(settlement[-1].replace(",", ""))

    return details

# --- Streamlit UI ---
st.title("📑 Loan SOA PDF Extractor → Excel")

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for uploaded_file in uploaded_files:
        text = extract_text_from_pdf(uploaded_file)
        details = parse_loan_details(text)
        data.append(details)

    df = pd.DataFrame(data)
    st.dataframe(df)

    # allow download
    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        "📥 Download Excel",
        data=output.getvalue(),
        file_name="loan_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
