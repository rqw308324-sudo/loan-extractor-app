import streamlit as st
import pandas as pd
import pdfplumber
import re
import calendar
from io import BytesIO

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

    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row = [str(x).strip() if x else "" for x in row]
                    row_text = " ".join(row)

                    if len(row) >= 7 and "UTNGR" in row[0]:
                        details["Loan No"] = row[0]
                        details["Loan Date"] = row[1]
                        details["Loan Amount"] = row[2].replace(",", "")
                        details["Loan Interest"] = row[3].replace(",", "")
                        try:
                            details["Agreement Value"] = str(float(details["Loan Amount"]) + float(details["Loan Interest"]))
                        except:
                            pass
                        details["Tenure in Months"] = row[4]
                        details["1st Installment Date"] = row[5]
                        details["Last Installment Date"] = row[6]

                    if "Receipt On Account" in row_text:
                        try:
                            amt = float(row[-1].replace(",", ""))
                            details["Receipt Amount"] = str((float(details["Receipt Amount"] or 0)) + amt)
                        except:
                            pass

                    if "Arrears As On" in row_text:
                        try:
                            details["Arrears Amount"] = row[-1].replace(",", "")
                        except:
                            pass

                    if "Settlement" in row_text:
                        try:
                            details["Settlement Total"] = row[-1].replace(",", "")
                        except:
                            pass

    # Regex-based text extraction
    cust = re.search(r"CUSTOMER DETAILS.*?Name\s*:(.+)", text, re.S)
    if cust:
        details["Customer Name"] = cust.group(1).splitlines()[0].strip()

    cust_addr = re.search(r"CUSTOMER DETAILS.*?Address\s*:(.+?)Mobile No", text, re.S)
    if cust_addr:
        details["Customer Address"] = cust_addr.group(1).replace("\n", " ").strip()

    cust_mobile = re.search(r"CUSTOMER DETAILS.*?Mobile No:([0-9]{6,})", text)
    if cust_mobile:
        details["Customer Mobile"] = cust_mobile.group(1)

    guar = re.search(r"GUARANTOR DETAILS.*?Name\s*:(.+)", text, re.S)
    if guar:
        details["Guarantor Name"] = guar.group(1).splitlines()[0].strip()

    guar_addr = re.search(r"GUARANTOR DETAILS.*?Address\s*:(.+?)Mobile No", text, re.S)
    if guar_addr:
        details["Guarantor Address"] = guar_addr.group(1).replace("\n", " ").strip()

    guar_mobile = re.search(r"GUARANTOR DETAILS.*?Mobile No:([0-9]{6,})", text)
    if guar_mobile:
        details["Guarantor Mobile"] = guar_mobile.group(1)

    # Branch
    branch = re.search(r"([A-Z]{2,})\s+UTNGR\d+", text)
    if branch:
        details["Branch"] = branch.group(1)

    # Loan Month & Year
    if details["Loan Date"]:
        try:
            d, m, y = details["Loan Date"].split("/")
            details["Loan Month"] = calendar.month_abbr[int(m)].upper()
            details["Loan Year"] = y
        except:
            pass

    return details

st.title("📑 Loan SOA PDF Extractor (Cloud-safe Hybrid)")

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for uploaded_file in uploaded_files:
        details = extract_details_from_pdf(uploaded_file)
        data.append(details)

    df = pd.DataFrame(data)
    st.dataframe(df)

    output = BytesIO()
    df.to_excel(output, index=False)
    st.download_button(
        label="📥 Download Excel",
        data=output.getvalue(),
        file_name="loan_details.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
