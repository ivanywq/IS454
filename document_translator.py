import fitz  # PyMuPDF for text extraction
import os
from openai import OpenAI
import pandas as pd
from io import StringIO

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

class InvoiceExtractor(DocumentExtractor):
    def extract_info(self):
        prompt = (
            "You are a document processing assistant. Extract information specifically for an Invoice.\n"
            "Identify and extract the following details in CSV format with exactly these columns:\n"
            "- Transaction_ID\n"
            "- Drug_Name\n"
            "- Quantity associated with each drug\n"
            "- Date administered, should be in DD.MM.YYYY (leave blank if not available)\n\n"
            "Provide the output in a CSV format with these columns in this order: Transaction_ID, Drug_Name, Quantity, Diagnosis.\n"
            "If there is a section labeled 'DRUGS / PRESCRIPTIONS / INJECTIONS', prioritize extracting items listed under it.\n\n"
            f"Here is the text:\n{self.text}\n"
            "Return only the CSV content with no extra explanations or commentary."
        )

        response = self._call_chatgpt(prompt)

        if response is None:
            print("Error: No response from ChatGPT")
            return None

        # Clean up response
        response = response.strip("```").strip()  # Remove markdown symbols and whitespace
        print("Raw response from ChatGPT:", response)

        # Remove any trailing lines that don't match CSV format
        cleaned_response = "\n".join([line for line in response.splitlines() if "," in line])

        # Try to parse the CSV-like output directly
        try:
            csv_data = pd.read_csv(StringIO(cleaned_response))
            return csv_data
        except pd.errors.ParserError as e:
            print("Error parsing CSV response:", e)
            return None

    def to_csv(self):
        # Get the output filename based on input filename
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        output_csv_path = f"{base_name}_extracted.csv"
        
        extracted_data = self.extract_info()
        
        if extracted_data is not None and not extracted_data.empty:
            extracted_data.to_csv(output_csv_path, index=False)
            print(f"Data successfully saved to {output_csv_path}")
        else:
            print("No data extracted to save or CSV is empty.")

# Other classes, adapted for structured extraction

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

class MedicalReportExtractor(DocumentExtractor):
    def extract_info(self):
        prompt = (
            "You are a document processing assistant. Extract information specifically for a Medical Report.\n"
            "Identify and extract:\n"
            "- Patient diagnosis\n"
            "- Treatment plan\n"
            "- Doctor’s notes\n"
            "- Consumable lists\n"
            "Here is the text:\n"
            f"{self.text}\n"
            "Provide the details in a structured CSV format with clear column headers."
        )
        return self._call_chatgpt(prompt)

# Example usage
def classify_and_extract_to_csv(pdf_path, document_type):
    if document_type == "Invoice":
        extractor = InvoiceExtractor(pdf_path)
        extractor.to_csv()
    else:
        print("Unknown document type")

# Example call
pdf_path = "test_pdf_splitting/output/1193 - 20-02_ocr_Invoice.pdf"
document_type = "Invoice"
classify_and_extract_to_csv(pdf_path, document_type)
