import streamlit as st
import pandas as pd
import re
import pdfplumber

def extract_details_from_pdf(file):
    details = {
        "Customer Name": "", "Customer Address": "", "Customer Mobile": "",
        "Guarantor Name": "", "Guarantor Address": "", "Guarantor Mobile": "",
        "Branch": "", "Loan No": "", "Loan Date": "", "Loan Month": "",
        "Loan Year": "", "Loan Amount": "", "Loan Interest": "",
        "Agreement Value": "", "Tenure in Months": "", "1st Installment Date": "",
        "Last Installment Date": "", "Receipt Amount": "", "Arrears Amount": "",
        "Settlement Total": ""
    }
    with pdfplumber.open(file) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"

    # Customer name and address (split properly)
    cust_match = re.search(r"Customer Name\s*:\s*(.+)", text)
    if cust_match:
        full_name = cust_match.group(1).strip()
        parts = full_name.split(" S/O")
        details["Customer Name"] = parts[0].strip()
        if len(parts) > 1:
            details["Customer Address"] = "S/O" + parts[1].strip()

    # Guarantor details
    guar_match = re.search(r"Guarantor Name\s*:\s*(.+)", text)
    if guar_match:
        full_guar = guar_match.group(1).strip()
        parts = full_guar.split(" S/O")
        details["Guarantor Name"] = parts[0].strip()
        if len(parts) > 1:
            details["Guarantor Address"] = "S/O" + parts[1].strip()

    # Mobile numbers
    cmobile = re.search(r"Customer Mobile\s*:\s*(\d+)", text)
    if cmobile:
        details["Customer Mobile"] = cmobile.group(1)
    gmobile = re.search(r"Guarantor Mobile\s*:\s*(\d+)", text)
    if gmobile:
        details["Guarantor Mobile"] = gmobile.group(1)

    # Branch
    branch = re.search(r"Branch\s*:\s*(\w+)", text)
    if branch:
        details["Branch"] = branch.group(1)

    # Loan info
    loan_no = re.search(r"Loan No\s*:\s*(\S+)", text)
    if loan_no:
        details["Loan No"] = loan_no.group(1)
    loan_date = re.search(r"Loan Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    if loan_date:
        details["Loan Date"] = loan_date.group(1)
        parts = loan_date.group(1).split("/")
        details["Loan Month"] = parts[1].replace("03", "MAR")
        details["Loan Year"] = parts[2]

    # Loan amounts
    lamount = re.search(r"Loan Amount\s*:\s*(\d+)", text)
    if lamount:
        details["Loan Amount"] = int(lamount.group(1))
    linterest = re.search(r"Loan Interest\s*:\s*(\d+)", text)
    if linterest:
        details["Loan Interest"] = int(linterest.group(1))
    if details["Loan Amount"] and details["Loan Interest"]:
        details["Agreement Value"] = int(details["Loan Amount"]) + int(details["Loan Interest"])

    # Tenure
    tenure = re.search(r"Tenure.*?(\d+)", text)
    if tenure:
        details["Tenure in Months"] = tenure.group(1)

    # Installments
    inst1 = re.search(r"1st Installment Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    if inst1:
        details["1st Installment Date"] = inst1.group(1)
    instlast = re.search(r"Last Installment Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
    if instlast:
        details["Last Installment Date"] = instlast.group(1)

    # Receipt Amount, Arrears, Settlement
    receipt = re.search(r"Receipt Amount\s*:?\s*(\d+)", text)
    if receipt:
        details["Receipt Amount"] = receipt.group(1)
    arrears = re.search(r"Arrears.*?(\d+)", text)
    if arrears:
        details["Arrears Amount"] = arrears.group(1)
    settlement = re.search(r"Settlement Total.*?(\d+)", text)
    if settlement:
        details["Settlement Total"] = settlement.group(1)

    return details

st.title("Loan PDF Extractor App")
uploaded_files = st.file_uploader("Upload SOA PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_data = []
    for uploaded_file in uploaded_files:
        with open(uploaded_file.name, "wb") as f:
            f.write(uploaded_file.getbuffer())
        data = extract_details_from_pdf(uploaded_file.name)
        all_data.append(data)

    df = pd.DataFrame(all_data)
    st.dataframe(df)

    # Export option
    excel_file = "loan_details.xlsx"
    df.to_excel(excel_file, index=False)
    with open(excel_file, "rb") as f:
        st.download_button("Download Excel", f, file_name=excel_file)
