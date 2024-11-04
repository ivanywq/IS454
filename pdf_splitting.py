import fitz  # PyMuPDF for text extraction
import PyPDF2
import os
import time
from openai import OpenAI

# Set your OpenAI API key
api_key = os.getenv("OPENAI_API_KEY")

# Create the OpenAI client instance
client = OpenAI(api_key=api_key)

def classify_page_with_chatgpt(page_text):
    try:
        if not page_text.strip():
            print('everything viewed as empty.')
            return "Medical Report"  # Default classification for empty pages

        # Improved prompt to force classification
        prompt = (
            "You are a document classification assistant. Your job is to categorize the given text "
            "into one of the following categories: \n"
            "1. Bill Audit Form\n"
            "2. Invoice\n"
            "3. Letter of Guarantee\n"
            "4. Medical Report\n\n"
            "Below are examples of each type:\n"
            "Bill Audit Form: This document contains information related to the auditing of a medical bill, "
            "such as patient details, itemized charges, and audit notes.\n"
            "Invoice: This document contains billing information, including line items, prices, discounts, and total amounts.\n"
            "Letter of Guarantee: This document is usually a formal letter ensuring payment or coverage, including names of guarantors, conditions, and details of the guarantee.\n"
            "Medical Report: This document contains medical information, including diagnosis, treatment, doctor's notes, and prescribed medications.\n\n"
            "Your task is to read the following page text and determine the most appropriate category for it. "
            "You must choose one of the four categories (Bill Audit Form, Invoice, Letter of Guarantee, Medical Report). "
            "Please make the best choice, even if it requires an educated guess. If you are unsure, choose 'Medical Report'.\n\n"
            f"Text: {page_text}\n\n"
            "Please provide only the category name as your answer."
        )

        # Make a request to the ChatGPT API using the client
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-3.5-turbo",
            max_tokens=20,
        )

        # Extract response content
        if chat_completion and hasattr(chat_completion, 'choices'):
            response_content = chat_completion.choices[0].message.content.strip()
            return response_content
        else:
            print("No valid response received.")
            return "Medical Report"  # Default classification if no valid response is received

    except Exception as e:
        print(f"Error during classification: {e}")
        return "Medical Report"  # Default classification in case of an error

def split_pdf_by_classification(input_pdf_path, output_directory):
    # Extract the base name of the input PDF file without extension
    input_filename = os.path.splitext(os.path.basename(input_pdf_path))[0]

    # Load the PDF
    try:
        pdf_document = fitz.open(input_pdf_path)
    except Exception as e:
        print(f"Error opening PDF: {e}")
        return

    classified_pages = {
        "Bill Audit Form": [],
        "Invoice": [],
        "Letter of Guarantee": [],
        "Medical Report": [],
    }

    # Classify each page using ChatGPT
    for page_number in range(len(pdf_document)):
        page = pdf_document.load_page(page_number)
        page_text = page.get_text()

        # Classify page using ChatGPT
        classification = classify_page_with_chatgpt(page_text)
        classified_pages[classification].append(page_number)
        print(f"Page {page_number + 1} classified as: {classification}")

        # Add delay to avoid rate limiting issues with OpenAI API
        time.sleep(1)

    # Split and save pages based on classification
    input_pdf = open(input_pdf_path, "rb")
    pdf_reader = PyPDF2.PdfReader(input_pdf)

    for category, pages in classified_pages.items():
        if not pages:
            continue

        pdf_writer = PyPDF2.PdfWriter()
        for page_number in pages:
            try:
                pdf_writer.add_page(pdf_reader.pages[page_number])
            except Exception as e:
                print(f"Error adding page {page_number + 1} to {category}: {e}")

        # Create the output path with the modified file name
        output_filename = f"{input_filename}_{category.replace(' ', '_')}.pdf"
        output_path = os.path.join(output_directory, output_filename)
        
        try:
            with open(output_path, "wb") as output_pdf:
                pdf_writer.write(output_pdf)
                print(f"Created: {output_path}")
        except Exception as e:
            print(f"Error writing {category} to file: {e}")

    input_pdf.close()

# Example usage
input_pdf_path = "test_pdf_splitting/1193 - 20-02_ocr.pdf"  # Specify the path to your PDF
output_directory = "test_pdf_splitting/output"  # Specify the path for output PDFs
os.makedirs(output_directory, exist_ok=True)
split_pdf_by_classification(input_pdf_path, output_directory)
