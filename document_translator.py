import fitz  # PyMuPDF for text extraction
import os
from openai import OpenAI
import pandas as pd
from io import StringIO
from collections import defaultdict

class DocumentExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        api_key = os.getenv("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
        self.text = self._load_pdf_text()

    def _load_pdf_text(self):
        text_content = []
        try:
            pdf_document = fitz.open(self.pdf_path)
            for page_num in range(pdf_document.page_count):
                page = pdf_document.load_page(page_num)
                text_content.append(page.get_text())
            pdf_document.close()
        except Exception as e:
            print(f"Error loading PDF: {e}")
        return "\n".join(text_content)

    def _call_chatgpt(self, prompt):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="gpt-4o-mini",
                max_tokens=5700
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error during API call: {e}")
            return None

class BillAuditFormExtractor(DocumentExtractor):
    def extract_info(self):
        prompt = (
            "You are a document processing assistant. Extract information specifically for a Bill Audit Form.\n"
            "Identify and extract:\n"
            "- Patient details\n"
            "- Itemized charges\n"
            "- Audit notes\n"
            "Here is the text:\n"
            f"{self.text}\n"
            "Provide the details in a structured CSV format with clear column headers."
        )
        return self._call_chatgpt(prompt)

class LetterOfGuaranteeExtractor(DocumentExtractor):
    def extract_info(self):
        prompt = (
            "You are a document processing assistant. Extract information specifically for a Letter of Guarantee.\n"
            "Identify and extract:\n"
            "- Names of guarantors\n"
            "- Coverage conditions\n"
            "- Guarantee details\n"
            "Here is the text:\n"
            f"{self.text}\n"
            "Provide the details in a structured CSV format with clear column headers."
        )
        return self._call_chatgpt(prompt)

class InvoiceExtractor(DocumentExtractor):
    def extract_info(self):
        base_name = os.path.basename(self.pdf_path)
        patient_id = base_name.split('_')[0].strip()  # Extract the first part of the filename
        prompt = (
            "You are a document processing assistant. Extract information specifically for an Invoice.\n"
            "Identify and extract the following details in CSV format with exactly these columns:\n"
            "- Transaction_ID (Use 'NA' if no transaction ID is available)\n"
            "- Drug/Services (This should include specific drugs, medications, warding details, medical procedures, scans, x-rays, etc., and should exclude generic terms such as 'Pharmacy Invoice' or 'Inpatient Invoice')\n"
            "- Quantity associated with each item\n"
            "- Date associated with each entry, in DD.MM.YYYY format (leave blank if not available)\n\n"
            "Only include rows where 'Drug/Services' refers to a specific drug or service. Do not include entries with generic terms such as 'Pharmacy Invoice' or 'Inpatient Invoice' in the 'Drug/Services' column.\n\n"
            "Provide the output in a CSV format with these columns in this order: Transaction_ID, Drug/Services, Quantity, Date.\n"
            f"Here is the text:\n{self.text}\n"
            "Return only the CSV content with no extra explanations or commentary."
        )

        response = self._call_chatgpt(prompt)

        if response is None:
            print("Error: No response from ChatGPT")
            return None

        # Clean up response and ensure Drug/Services with commas are handled correctly
        response = response.replace("```csv", "").replace("```", "").strip()
        print("Raw response from ChatGPT:", response)

        cleaned_response = []
        for line in response.splitlines():
            if line.count(",") >= 3:
                parts = line.split(',')

                transaction_id = parts[0].strip()
                drug_name = ",".join(parts[1:-2]).strip()  # Join parts in case of extra commas in Drug/Services
                quantity = parts[-2].strip()
                date_administered = parts[-1].strip()

                # Enclose drug_name in quotes to avoid issues with internal commas
                cleaned_line = f'{transaction_id},"{drug_name}",{quantity},{date_administered}'
                cleaned_response.append(cleaned_line)
            else:
                continue

        cleaned_response = "\n".join(cleaned_response)

        try:
            csv_data = pd.read_csv(StringIO(cleaned_response), quotechar='"')
            csv_data["patient_id"] = patient_id  # Add patient_id column
            print("Invoice Data successfully extracted and stored in DataFrame.")
            print(csv_data)  # Print the DataFrame for verification
            return csv_data
        except pd.errors.ParserError as e:
            print("Error parsing CSV response:", e)
            return None

class MedicalReportExtractor(DocumentExtractor):
    def extract_info(self):
        base_name = os.path.basename(self.pdf_path)
        patient_id = base_name.split('_')[0].strip()  # Extract the first part of the filename

        prompt = (
            "You are a document processing assistant. Extract all overarching diagnoses from a Medical Report.\n"
            "Identify and extract all primary diagnosed conditions in CSV format with exactly these columns:\n"
            "- Diagnosis (description of the medical condition, focusing on overarching or primary diagnoses rather than specific details)\n"
            "- Diagnosis Type (classification of the diagnosis based on ICD-10 categories, e.g., 'I21 - Acute myocardial infarction')\n\n"
            "Be especially attentive to phrases that indicate a diagnosis, such as 'diagnosed with', 'suffers from', 'presents with', 'history of', 'indicates', or 'suggests'.\n"
            "If there are multiple conditions, list each overarching diagnosis on a separate line in the output.\n\n"
            "Use the ICD-10 classification to categorize each diagnosis in the 'Diagnosis Type' column, providing the full ICD-10 code and description (e.g., 'I21 - Acute myocardial infarction').\n\n"
            "Provide the output in a CSV format with columns labeled 'Diagnosis', 'Diagnosis Type' without any extra symbols or Markdown syntax. If a value contains commas, enclose it in double quotes.\n\n"
            f"Here is the text:\n{self.text}\n"
            "Return only the CSV content with no extra explanations or commentary."
        )

        response = self._call_chatgpt(prompt)

        if response is None:
            print("Error: No response from ChatGPT")
            return None

        # Clean up response to remove any Markdown syntax or extra symbols
        response = response.replace("```csv", "").replace("```", "").strip()
        print("Cleaned response from ChatGPT:", response)

        # Parse the CSV-like response into DataFrame and add patient_id
        try:
            # Use the 'quotechar' parameter to handle any quotes around Diagnosis or Diagnosis Type
            csv_data = pd.read_csv(StringIO(response), quotechar='"')
            csv_data["patient_id"] = patient_id  # Add patient_id column
            print("Medical Report Data successfully extracted and stored in DataFrame.")
            print(csv_data)  # Print the DataFrame for verification
            return csv_data
        except pd.errors.ParserError as e:
            print("Error parsing CSV response:", e)
            print("Attempting to clean and reformat response for parsing...")

            # Attempt to reformat and clean data if there are issues with parsing
            cleaned_response = []
            for line in response.splitlines():
                parts = line.split(',')

                # Ensure Diagnosis and Diagnosis Type are quoted if they contain commas
                diagnosis = parts[0].strip()
                diagnosis_type = parts[1].strip() if len(parts) > 1 else ""
                
                if ',' in diagnosis:
                    diagnosis = f'"{diagnosis}"'
                if ',' in diagnosis_type:
                    diagnosis_type = f'"{diagnosis_type}"'

                cleaned_line = f"{diagnosis},{diagnosis_type}"
                cleaned_response.append(cleaned_line)

            # Join cleaned lines and parse again
            cleaned_response = "\n".join(cleaned_response)
            try:
                csv_data = pd.read_csv(StringIO(cleaned_response), quotechar='"')
                csv_data["patient_id"] = patient_id  # Add patient_id column
                print("Medical Report Data successfully extracted and stored in DataFrame after cleaning.")
                print(csv_data)  # Print the DataFrame for verification
                return csv_data
            except pd.errors.ParserError as e:
                print("Error parsing cleaned CSV response:", e)
                return None


# Helper function to process both Invoices and Medical Reports and combine them
# Main function to process and combine files with the same patient ID
def process_and_combine(pdfs_folder, output_folder):
    os.makedirs(output_folder, exist_ok=True)

    # Group files by the starting name (patient ID)
    files_by_patient_id = defaultdict(list)
    for filename in os.listdir(pdfs_folder):
        if filename.endswith(".pdf"):
            patient_id = filename.split('_')[0].strip()
            files_by_patient_id[patient_id].append(filename)

    # Process each group of files with the same starting name (patient ID)
    for patient_id, files in files_by_patient_id.items():
        invoice_df = None
        medical_report_df = None

        # Extract data for each file type
        for filename in files:
            pdf_path = os.path.join(pdfs_folder, filename)
            if filename.endswith("Invoice.pdf"):
                invoice_extractor = InvoiceExtractor(pdf_path)
                invoice_df = invoice_extractor.extract_info()
            elif filename.endswith("Medical_Report.pdf"):
                medical_report_extractor = MedicalReportExtractor(pdf_path)
                medical_report_df = medical_report_extractor.extract_info()

        # Only combine if both invoice and medical report data are available
        if invoice_df is not None and medical_report_df is not None:
            # Ensure columns are correctly formatted
            invoice_df["patient_id"] = invoice_df["patient_id"].astype(str)
            medical_report_df["patient_id"] = medical_report_df["patient_id"].astype(str)

            # Merge on patient_id and save as a single CSV
            combined_df = pd.merge(invoice_df, medical_report_df, on="patient_id", how="outer")
            combined_df = combined_df[['patient_id', 'Transaction_ID', 'Date', 'Drug/Services', 'Quantity', 'Diagnosis', 'Diagnosis Type']]
            
            output_path = os.path.join(output_folder, f"{patient_id}_transformed_data.csv")
            combined_df.to_csv(output_path, index=False)
            print(f"Combined data saved to {output_path}")
        else:
            print(f"Skipping combination for patient ID {patient_id}: Missing either Invoice or Medical Report.")


# Example usage for all PDFs in a folder
pdfs_folder = "test_pdf_splitting/new_output_test"
output_folder = 'extracted_csv'
process_and_combine(pdfs_folder, output_folder)
