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

        # Regex-based extraction for text details
        cust_match = re.search(r"Customer Name\s*:\s*(.+)", text)
        if cust_match:
            full_name = cust_match.group(1).strip()
            parts = full_name.split(" S/O")
            details["Customer Name"] = parts[0].strip()
            if len(parts) > 1:
                details["Customer Address"] = "S/O" + parts[1].strip()

        guar_match = re.search(r"Guarantor Name\s*:\s*(.+)", text)
        if guar_match:
            full_guar = guar_match.group(1).strip()
            parts = full_guar.split(" S/O")
            details["Guarantor Name"] = parts[0].strip()
            if len(parts) > 1:
                details["Guarantor Address"] = "S/O" + parts[1].strip()

        cmobile = re.search(r"Customer Mobile\s*:\s*(\d+)", text)
        if cmobile:
            details["Customer Mobile"] = cmobile.group(1)
        gmobile = re.search(r"Guarantor Mobile\s*:\s*(\d+)", text)
        if gmobile:
            details["Guarantor Mobile"] = gmobile.group(1)

        branch = re.search(r"Branch\s*:\s*(\w+)", text)
        if branch:
            details["Branch"] = branch.group(1)

        loan_no = re.search(r"Loan No\s*:\s*(\S+)", text)
        if loan_no:
            details["Loan No"] = loan_no.group(1)

        loan_date = re.search(r"Loan Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
        if loan_date:
            details["Loan Date"] = loan_date.group(1)
            parts = loan_date.group(1).split("/")
            details["Loan Month"] = parts[1].replace("03", "MAR")
            details["Loan Year"] = parts[2]

        tenure = re.search(r"Tenure.*?(\d+)", text)
        if tenure:
            details["Tenure in Months"] = tenure.group(1)

        inst1 = re.search(r"1st Installment Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
        if inst1:
            details["1st Installment Date"] = inst1.group(1)
        instlast = re.search(r"Last Installment Date\s*:\s*(\d{2}/\d{2}/\d{4})", text)
        if instlast:
            details["Last Installment Date"] = instlast.group(1)

        # Table-based extraction for numeric values
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    row_text = " ".join([str(cell) for cell in row if cell])
                    if "Loan Amount" in row_text and details["Loan Amount"] == "":
                        amt = re.search(r"(\d+)", row_text)
                        if amt: details["Loan Amount"] = amt.group(1)
                    if "Interest" in row_text and details["Loan Interest"] == "":
                        intr = re.search(r"(\d+)", row_text)
                        if intr: details["Loan Interest"] = intr.group(1)
                    if "Agreement" in row_text and details["Agreement Value"] == "":
                        agr = re.search(r"(\d+)", row_text)
                        if agr: details["Agreement Value"] = agr.group(1)
                    if "Receipt" in row_text and details["Receipt Amount"] == "":
                        rec = re.search(r"(\d+)", row_text)
                        if rec: details["Receipt Amount"] = rec.group(1)
                    if "Arrears" in row_text and details["Arrears Amount"] == "":
                        arr = re.search(r"(\d+)", row_text)
                        if arr: details["Arrears Amount"] = arr.group(1)
                    if "Settlement" in row_text and details["Settlement Total"] == "":
                        sett = re.search(r"(\d+)", row_text)
                        if sett: details["Settlement Total"] = sett.group(1)

        # If Agreement not found, calculate manually
        if details["Loan Amount"] and details["Loan Interest"] and not details["Agreement Value"]:
            try:
                details["Agreement Value"] = str(int(details["Loan Amount"]) + int(details["Loan Interest"]))
            except:
                pass

    return details

st.title("Loan PDF Extractor App (Hybrid Regex + Table)")
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
