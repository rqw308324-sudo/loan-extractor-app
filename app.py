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

# --- Parse details (basic, for testing) ---
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
        "Receipt Amount": None,
        "Arrears Amount": None,
        "Settlement Total": None
    }

    # Simple regex patterns (to be tuned based on debug output)
    cust_name = re.search(r"Name\s*:\s*(.+)", text)
    if cust_name:
        details["Customer Name"] = cust_name.group(1).split("\n")[0].strip()

    cust_mobile = re.search(r"Mobile No:\s*([0-9]{6,})", text)
    if cust_mobile:
        details["Customer Mobile"] = cust_mobile.group(1)

    loan_no = re.search(r"(UTNGR\d+)", text)
    if loan_no:
        details["Loan No"] = loan_no.group(1)

    loan_date = re.search(r"(\d{2}/\d{2}/\d{4})", text)
    if loan_date:
        details["Loan Date"] = loan_date.group(1)

    loan_amount = re.search(r"Loan Amount\s*:?([\d,]+\.\d{2})", text)
    if loan_amount:
        details["Loan Amount"] = float(loan_amount.group(1).replace(",", ""))

    loan_interest = re.search(r"Loan Interest\s*:?([\d,]+\.\d{2})", text)
    if loan_interest:
        details["Loan Interest"] = float(loan_interest.group(1).replace(",", ""))

    if details["Loan Amount"] and details["Loan Interest"]:
        details["Agreement Value"] = details["Loan Amount"] + details["Loan Interest"]

    receipts = re.findall(r"Receipt On Account.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)
    if receipts:
        details["Receipt Amount"] = sum(float(r.replace(",", "")) for r in receipts)

    arrears = re.search(r"Arrears As On.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)
    if arrears:
        details["Arrears Amount"] = float(arrears.group(1).replace(",", ""))

    settlement = re.search(r"Settlement.*?(\d{1,3}(?:,\d{3})*(?:\.\d{2}))", text)
    if settlement:
        details["Settlement Total"] = float(settlement.group(1).replace(",", ""))

    return details


# --- Streamlit UI ---
st.title("📑 Loan SOA PDF Extractor → Debug Mode")

uploaded_files = st.file_uploader("Upload SOA PDFs", type=["pdf"], accept_multiple_files=True)

if uploaded_files:
    data = []
    for uploaded_file in uploaded_files:
        text = extract_text_from_pdf(uploaded_file)

        # 🔍 Debug: Show extracted text
        st.subheader(f"Extracted Text: {uploaded_file.name}")
        st.text_area("Raw Text", text[:2000])  # first 2000 chars only

        # Parse details
        details = parse_loan_details(text)
        data.append(details)

        # Also allow download of raw text
        st.download_button(
            label=f"Download Extracted Text ({uploaded_file.name})",
            data=text,
            file_name=uploaded_file.name.replace(".pdf", ".txt"),
            mime="text/plain"
        )

    df = pd.DataFrame(data)
    st.subheader("Parsed Data Preview")
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
