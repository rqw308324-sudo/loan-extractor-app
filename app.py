import streamlit as st
import pandas as pd
import pdfplumber
import re
import calendar
from io import BytesIO

st.title("📑 Loan SOA Extractor (Final Version)")

def extract_details_from_pdf(uploaded_file):
    details = {
        "Customer Name": "", "Customer Address": "", "Customer Mobile": "",
        "Guarantor Name": "", "Guarantor Address": "", "Guarantor Mobile": "",
        "Branch": "", "Loan No": "", "Loan Date": "", "Loan Month": "",
        "Loan Year": "", "Loan Amount": "", "Loan Interest": "",
        "Agreement Value": "", "Tenure in Months": "", "1st Installment Date": "",
        "Last Installment Date": "", "Receipt Amount": "", "Arrears Amount": "",
        "Settlement Total": ""
    }

    text = ""
    with pdfplumber.open(uploaded_file) as pdf:
        for page in pdf.pages:
            txt = page.extract_text()
            if txt:
                text += txt + "\n"

    # Customer details
    cust_name = re.search(r"CUSTOMER DETAILS.*?Name\s*:\s*(.+)", text, re.S)
    if cust_name:
        details["Customer Name"] = cust_name.group(1).splitlines()[0].strip()
    cust_addr = re.search(r"CUSTOMER DETAILS.*?Address\s*:(.+?)Mobile No", text, re.S)
    if cust_addr:
        details["Customer Address"] = cust_addr.group(1).replace("\n", " ").strip()
    cust_mobile = re.search(r"CUSTOMER DETAILS.*?Mobile No:?\s*([0-9]{6,})", text)
    if cust_mobile:
        details["Customer Mobile"] = cust_mobile.group(1)

    # Guarantor details
    guar_name = re.search(r"GUARANTOR DETAILS.*?Name\s*:\s*(.+)", text, re.S)
    if guar_name:
        details["Guarantor Name"] = guar_name.group(1).splitlines()[0].strip()
    guar_addr = re.search(r"GUARANTOR DETAILS.*?Address\s*:(.+?)Mobile No", text, re.S)
    if guar_addr:
        details["Guarantor Address"] = guar_addr.group(1).replace("\n", " ").strip()
    guar_mobile = re.search(r"GUARANTOR DETAILS.*?Mobile No:?\s*([0-9]{6,})", text)
    if guar_mobile:
        details["Guarantor Mobile"] = guar_mobile.group(1)

    # Loan summary row
    loan_match = re.search(r"(UTNGR\d+)\s+(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4}).*?(\d{2}/\d{2}/\d{4})", text)
    if loan_match:
        details["Loan No"] = loan_match.group(1)
        details["Loan Date"] = loan_match.group(2)
        details["1st Installment Date"] = loan_match.group(3)
        details["Last Installment Date"] = loan_match.group(4)
        # Branch from Loan No prefix
        details["Branch"] = re.match(r"(UTNGR)", loan_match.group(1)).group(1)

    # Loan amounts
    amounts = re.findall(r"(\d{1,3}(?:,\d{3})*\.\d{2})", text)
    # heuristic: Loan Amount + Interest appear together (50000.00 13360.00)
    amt_match = re.search(r"(\d{2,}\.?\d*)\s+(\d{2,}\.?\d*)\s+\d{1,2}\s+\d{2}/\d{2}/\d{4}", text)
    if amt_match:
        details["Loan Amount"] = amt_match.group(1).replace(",", "")
        details["Loan Interest"] = amt_match.group(2).replace(",", "")
        try:
            details["Agreement Value"] = str(float(details["Loan Amount"]) + float(details["Loan Interest"]))
        except:
            pass

    # Tenure
    tenure = re.search(r"(\d{1,2})\s+\d{2}/\d{2}/\d{4}\s+\d{2}/\d{2}/\d{4}", text)
    if tenure:
        details["Tenure in Months"] = tenure.group(1)

    # Arrears
    arrears = re.search(r"Arrears As On.*?(\d{1,3}(?:,\d{3})*\.\d{2})", text)
    if arrears:
        details["Arrears Amount"] = arrears.group(1).replace(",", "")

    # Settlement Total
    settlement = re.search(r"Settlement.*?(\d{1,3}(?:,\d{3})*\.\d{2})", text)
    if settlement:
        details["Settlement Total"] = settlement.group(1).replace(",", "")

    # Receipt total (look for 'Total' after receipts)
    receipt_total = re.search(r"Total.*?(\d{1,3}(?:,\d{3})*\.\d{2})", text)
    if receipt_total:
        details["Receipt Amount"] = receipt_total.group(1).replace(",", "")

    # Loan Month/Year
    if details["Loan Date"]:
        try:
            d, m, y = details["Loan Date"].split("/")
            details["Loan Month"] = calendar.month_abbr[int(m)].upper()
            details["Loan Year"] = y
        except:
            pass

    return details

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for uploaded_file in uploaded_files:
        details = extract_details_from_pdf(uploaded_file)
        data.append(details)
    df = pd.DataFrame(data)
    st.dataframe(df)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Loans")
    st.download_button("📥 Download Excel", data=output.getvalue(),
                       file_name="loan_details.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
