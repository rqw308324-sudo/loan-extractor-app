import streamlit as st
import pandas as pd
import pdfplumber
import re
import calendar
from io import BytesIO

def extract_details(file):
    details = {
        "Customer Name": None,
        "Customer Address": None,
        "Customer Mobile": None,
        "Guarantor Name": None,
        "Guarantor Address": None,
        "Guarantor Mobile": None,
        "Branch": None,
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

    text = ""
    with pdfplumber.open(file) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

            # Extract tables
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row = [str(x).strip() if x else "" for x in row]

                    # Loan summary row
                    if len(row) >= 7 and "UTNGR" in row[0]:
                        details["Loan No"] = row[0]
                        details["Loan Date"] = row[1]
                        details["Loan Amount"] = float(row[2].replace(",", ""))
                        details["Loan Interest"] = float(row[3].replace(",", ""))
                        details["Agreement Value"] = details["Loan Amount"] + details["Loan Interest"]
                        details["Tenure in Months"] = int(row[4])
                        details["1st Installment Date"] = row[5]
                        details["Last Installment Date"] = row[6]

                    # Receipts (sum)
                    if "Receipt On Account" in " ".join(row):
                        try:
                            amt = float(row[-1].replace(",", ""))
                            details["Receipt Amount"] = (details["Receipt Amount"] or 0) + amt
                        except:
                            pass

                    # Arrears
                    if "Arrears As On" in " ".join(row):
                        try:
                            details["Arrears Amount"] = float(row[-1].replace(",", ""))
                        except:
                            pass

                    # Settlement
                    if "Settlement" in " ".join(row):
                        try:
                            details["Settlement Total"] = float(row[-1].replace(",", ""))
                        except:
                            pass

    # --- Branch ---
    branch = re.search(r"([A-Z]{2,})\s+UTNGR\d+", text)
    if branch:
        details["Branch"] = branch.group(1)

    # --- Customer ---
    cust_name = re.search(r"CUSTOMER DETAILS.*?Name\s*:(.+)", text, re.S)
    if cust_name:
        details["Customer Name"] = cust_name.group(1).splitlines()[0].strip()

    cust_addr = re.search(r"CUSTOMER DETAILS.*?Address\s*:(.+?)Mobile No", text, re.S)
    if cust_addr:
        details["Customer Address"] = cust_addr.group(1).replace("\n", " ").strip()

    cust_mobile = re.search(r"CUSTOMER DETAILS.*?Mobile No:([0-9]{6,})", text)
    if cust_mobile:
        details["Customer Mobile"] = cust_mobile.group(1)

    # --- Guarantor ---
    guar_name = re.search(r"GUARANTOR DETAILS.*?Name\s*:(.+)", text, re.S)
    if guar_name:
        details["Guarantor Name"] = guar_name.group(1).splitlines()[0].strip()

    guar_addr = re.search(r"GUARANTOR DETAILS.*?Address\s*:(.+?)Mobile No", text, re.S)
    if guar_addr:
        details["Guarantor Address"] = guar_addr.group(1).replace("\n", " ").strip()

    guar_mobile = re.search(r"GUARANTOR DETAILS.*?Mobile No:([0-9]{6,})", text)
    if guar_mobile:
        details["Guarantor Mobile"] = guar_mobile.group(1)

    # --- Loan Month & Year ---
    if details["Loan Date"]:
        try:
            d, m, y = details["Loan Date"].split("/")
            details["Loan Month"] = calendar.month_abbr[int(m)].upper()
            details["Loan Year"] = y
        except:
            pass

    return details


st.title("📑 Loan SOA PDF Extractor → Final Version")

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for uploaded_file in uploaded_files:
        details = extract_details(uploaded_file)
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
