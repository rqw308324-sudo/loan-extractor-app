import streamlit as st
import pandas as pd
import re
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import tempfile
import os

def extract_text_from_pdf(pdf_file):
    text = ""
    with tempfile.TemporaryDirectory() as path:
        images = convert_from_path(pdf_file, dpi=300, output_folder=path)
        for img in images:
            text += pytesseract.image_to_string(img, lang="eng") + "\n"
    return text

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
    
    text = extract_text_from_pdf(file)

    # Regex-based extraction
    cust_match = re.search(r"Customer Name\s*:?\s*(.+)", text)
    if cust_match:
        full_name = cust_match.group(1).strip()
        parts = full_name.split(" S/O")
        details["Customer Name"] = parts[0].strip()
        if len(parts) > 1:
            details["Customer Address"] = "S/O" + parts[1].strip()

    guar_match = re.search(r"Guarantor Name\s*:?\s*(.+)", text)
    if guar_match:
        full_guar = guar_match.group(1).strip()
        parts = full_guar.split(" S/O")
        details["Guarantor Name"] = parts[0].strip()
        if len(parts) > 1:
            details["Guarantor Address"] = "S/O" + parts[1].strip()

    cmobile = re.search(r"Customer Mobile\s*:?\s*(\d+)", text)
    if cmobile:
        details["Customer Mobile"] = cmobile.group(1)
    gmobile = re.search(r"Guarantor Mobile\s*:?\s*(\d+)", text)
    if gmobile:
        details["Guarantor Mobile"] = gmobile.group(1)

    branch = re.search(r"Branch\s*:?\s*(\w+)", text)
    if branch:
        details["Branch"] = branch.group(1)

    loan_no = re.search(r"Loan No\s*:?\s*(\S+)", text)
    if loan_no:
        details["Loan No"] = loan_no.group(1)

    loan_date = re.search(r"Loan Date\s*:?\s*(\d{2}/\d{2}/\d{4})", text)
    if loan_date:
        details["Loan Date"] = loan_date.group(1)
        parts = loan_date.group(1).split("/")
        details["Loan Month"] = parts[1].replace("03", "MAR")
        details["Loan Year"] = parts[2]

    lamount = re.search(r"Loan Amount\s*:?\s*(\d+)", text)
    if lamount:
        details["Loan Amount"] = lamount.group(1)

    linterest = re.search(r"Loan Interest\s*:?\s*(\d+)", text)
    if linterest:
        details["Loan Interest"] = linterest.group(1)

    if details["Loan Amount"] and details["Loan Interest"]:
        try:
            details["Agreement Value"] = str(int(details["Loan Amount"]) + int(details["Loan Interest"]))
        except:
            pass

    tenure = re.search(r"Tenure.*?(\d+)", text)
    if tenure:
        details["Tenure in Months"] = tenure.group(1)

    inst1 = re.search(r"1st Installment Date\s*:?\s*(\d{2}/\d{2}/\d{4})", text)
    if inst1:
        details["1st Installment Date"] = inst1.group(1)

    instlast = re.search(r"Last Installment Date\s*:?\s*(\d{2}/\d{2}/\d{4})", text)
    if instlast:
        details["Last Installment Date"] = instlast.group(1)

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

st.title("Loan PDF Extractor App (OCR-based)")
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

    excel_file = "loan_details.xlsx"
    df.to_excel(excel_file, index=False)
    with open(excel_file, "rb") as f:
        st.download_button("Download Excel", f, file_name=excel_file)
