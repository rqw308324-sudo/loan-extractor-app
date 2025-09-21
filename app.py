import streamlit as st
import pandas as pd
import pdfplumber
import re
import calendar
from io import BytesIO

st.set_page_config(page_title="Loan SOA Extractor", layout="wide")

def parse_money(s):
    """Return a numeric string cleaned of commas; prefer numbers with decimals when present."""
    if not s: return ""
    s = str(s).strip()
    # Find the longest numeric-like token (with optional commas and decimals)
    m = re.findall(r"[\d]{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+", s)
    if not m: return ""
    # prefer token that contains decimal, otherwise first
    for token in m:
        if "." in token:
            return token.replace(",", "")
    return m[0].replace(",", "")

def sum_receipts_from_table(table):
    total = 0.0
    found = False
    for row in table:
        # flatten row cells to text
        row_text = " ".join([str(c) for c in row if c])
        if "Receipt" in row_text or "Receipt On Account" in row_text:
            # try last numeric in row
            nums = re.findall(r"[\d]{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+", row_text)
            if nums:
                val = float(nums[-1].replace(",", ""))
                total += val
                found = True
    return (total if found else None)

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
    try:
        with pdfplumber.open(file) as pdf:
            # Gather full extracted text for regex-based fields
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    text += txt + "\n"

            # Table-based extraction (scan all tables for loan/transactions)
            with pdfplumber.open(file) as pdf2:
                for page in pdf2.pages:
                    tables = page.extract_tables() or []
                    for table in tables:
                        # normalize rows
                        for row in table:
                            # join row for easier checks
                            row_text = " ".join([str(c).strip() for c in row if c is not None and str(c).strip() != ""])
                            # Loan summary row detection (UTNGR)
                            if any(cell and "UTNGR" in str(cell) for cell in row):
                                # try to pick loan no from any cell containing UTNGR
                                for cell in row:
                                    if cell and "UTNGR" in str(cell):
                                        details["Loan No"] = str(cell).strip()
                                        break
                                # try to extract date and amounts from nearby cells
                                # pick numeric/date tokens from row_text
                                date_match = re.search(r"\d{2}/\d{2}/\d{4}", row_text)
                                if date_match:
                                    details["Loan Date"] = date_match.group(0)
                                # find all money tokens
                                money_tokens = re.findall(r"[\d]{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+", row_text)
                                # Heuristic: after date, next two numeric tokens are loan amount and interest
                                if date_match and money_tokens:
                                    # find index of date in sequence by tokenizing row_text
                                    # fallback: take first two numeric tokens as amounts
                                    nums = [t.replace(",", "") for t in money_tokens]
                                    if len(nums) >= 2:
                                        details["Loan Amount"] = nums[0]
                                        details["Loan Interest"] = nums[1]
                                        try:
                                            details["Agreement Value"] = str(float(details["Loan Amount"]) + float(details["Loan Interest"]))
                                        except:
                                            pass
                            # Receipt rows sum
                            if "Receipt" in row_text:
                                try:
                                    nums = re.findall(r"[\d]{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+", row_text)
                                    if nums:
                                        val = float(nums[-1].replace(",", ""))
                                        if details["Receipt Amount"] == "":
                                            details["Receipt Amount"] = 0.0
                                        details["Receipt Amount"] = float(details["Receipt Amount"]) + val
                                except:
                                    pass
                            # Arrears detection
                            if "Arrears As On" in row_text or row_text.strip().startswith("Arrears As On"):
                                nums = re.findall(r"[\d]{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+", row_text)
                                if nums:
                                    details["Arrears Amount"] = nums[-1].replace(",", "")
                            # Settlement detection lines (III - Settlement Amount)
                            if "III - Settlement" in row_text or "Settlement Amount" in row_text or (row_text.strip().startswith("Total") and len(row) >= 3):
                                nums = re.findall(r"[\d]{1,3}(?:[,]\d{3})*(?:\.\d{2})?|\d+\.\d{2}|\d+", row_text)
                                if nums:
                                    details["Settlement Total"] = nums[-1].replace(",", "")

    except Exception as e:
        st.warning("Warning while reading PDF tables: " + str(e))

    # Regex-based extraction for text blocks (customer/guarantor etc.)
    try:
        cust = re.search(r"CUSTOMER DETAILS.*?Name\\s*:\\s*(.+)", text, re.S|re.I)
        if cust:
            name_line = cust.group(1).splitlines()[0].strip()
            # split off S/O W/O D/O into address piece if present
            m = re.split(r"\b(S/?O|W/?O|D/?O)\b", name_line, flags=re.I)
            details["Customer Name"] = m[0].strip()
            if len(m) > 1:
                details["Customer Address"] = " ".join(m[1:]).strip()

        cust_addr = re.search(r"CUSTOMER DETAILS.*?Address\\s*:(.+?)Mobile No", text, re.S|re.I)
        if cust_addr:
            details["Customer Address"] = " ".join([l.strip() for l in cust_addr.group(1).splitlines() if l.strip()])

        cust_mobile = re.search(r"CUSTOMER DETAILS.*?Mobile No\\s*:\\s*([0-9]{6,})", text, re.S|re.I)
        if cust_mobile:
            details["Customer Mobile"] = cust_mobile.group(1)

        guar = re.search(r"GUARANTOR DETAILS.*?Name\\s*:\\s*(.+)", text, re.S|re.I)
        if guar:
            details["Guarantor Name"] = guar.group(1).splitlines()[0].strip()

        guar_addr = re.search(r"GUARANTOR DETAILS.*?Address\\s*:(.+?)Mobile No", text, re.S|re.I)
        if guar_addr:
            details["Guarantor Address"] = " ".join([l.strip() for l in guar_addr.group(1).splitlines() if l.strip()])

        guar_mobile = re.search(r"GUARANTOR DETAILS.*?Mobile No\\s*:\\s*([0-9]{6,})", text, re.S|re.I)
        if guar_mobile:
            details["Guarantor Mobile"] = guar_mobile.group(1)

        # Branch
        branch = re.search(r"([A-Z]{2,})\\s+UTNGR\\d+", text)
        if branch:
            details["Branch"] = branch.group(1)

        # Loan Date parse month/year
        if details["Loan Date"]:
            try:
                d,m,y = details["Loan Date"].split("/")
                details["Loan Month"] = calendar.month_abbr[int(m)].upper()
                details["Loan Year"] = y
            except:
                pass

        # convert numeric fields to clean numeric strings
        for k in ["Loan Amount","Loan Interest","Agreement Value","Receipt Amount","Arrears Amount","Settlement Total"]:
            if details.get(k) not in (None, ""):
                details[k] = parse_money(details[k])

    except Exception as e:
        st.warning("Warning while parsing text fields: " + str(e))

    return details

st.title("📑 Loan SOA Extractor — Cloud-safe (Final)")
st.caption("Uploads: multiple PDFs → Extract Customer/Guarantor/Loan/Amounts → Download Excel")

uploaded = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded:
    rows = []
    for f in uploaded:
        # streamlit gives a file-like object; write to temp file because pdfplumber expects a path-like or file object
        with open(f.name, "wb") as tmpf:
            tmpf.write(f.getbuffer())
        row = extract_details_from_pdf(f.name)
        rows.append(row)

    df = pd.DataFrame(rows)
    st.dataframe(df.fillna(""))

    # Excel download in-memory (fixed)
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Loans")
    data = output.getvalue()
    st.download_button("📥 Download Excel", data=data, file_name="loan_details.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
