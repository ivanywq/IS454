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

        prompt = (
            "You are a highly advanced document classification assistant. Your task is to categorize the following page text into one of four categories: "
            "1. Bill Audit Form\n"
            "2. Invoice\n"
            "3. Letter of Guarantee\n"
            "4. Medical Report\n\n"
            "Carefully analyze the provided text and categorize it based on the following detailed guidelines:\n\n"
            "**Bill Audit Form**:\n"
            "- Primarily focuses on **auditing** medical bills.\n"
            "- Includes **patient details**, **itemized charges**, and **audit notes**.\n"
            "- Look for terms like 'audit', 'reconciliation', 'review', 'charges audited', or 'summary of charges'.\n"
            "- **Important**: If the text starts with a company stamp, hospital logo, or hospital name, this document is **less likely** to be a Bill Audit Form.\n\n"
            "**Invoice**:\n"
            "- Used for **billing purposes**, listing items, prices, discounts, and total amounts.\n"
            "- Should contain key terms like **'Invoice Number'**, **'Tax Invoice'**, **'Due Date'**, or **'Payment Due'**.\n"
            "- Typically focuses on **payment information**.\n"
            "- If the document starts with a **hospital stamp or logo**, consider this first as an Invoice rather than a Bill Audit Form, particularly if billing-related keywords are present.\n"
            "- **Important**: Do not classify documents with lists of consumables, medical supplies, or inventory items as Invoice; instead, categorize them as Medical Report.\n\n"
            "**Letter of Guarantee**:\n"
            "- A formal document ensuring **payment or coverage** from an insurer or healthcare provider.\n"
            "- Look for terms like 'guarantee', 'coverage', 'guarantor', 'terms of coverage', or 'formal letter'.\n"
            "- Typically includes **names, conditions, and guarantees**.\n\n"
            "**Medical Report**:\n"
            "- Contains detailed medical information such as **diagnosis**, **treatment**, **clinical notes**, and **patient history**.\n"
            "- Look for terms like 'diagnosis', 'treatment plan', 'medical history', 'clinical notes', or 'symptoms'.\n"
            "- Usually includes **doctor’s notes**, **patient health information**, or **treatment details**.\n"
            "- **Important**: If the document contains consumable lists, medical supplies, or references to items used during treatment, categorize it as Medical Report.\n\n"
            "To classify each page:\n"
            "1. Analyze the **overall context** of the text, including phrases, sections, and headers.\n"
            "2. Pay close attention to **key terms** and **the absence of expected words** (e.g., missing 'Tax Invoice' should raise suspicion of a misclassification).\n"
            "3. If the document starts with a **hospital name, logo, or stamp**, it is more likely to be an **Invoice** or **Medical Report**.\n"
            "4. If unsure and if the text includes **hospital-related information** but lacks clear audit or billing indicators, consider classifying it as a **Medical Report**.\n\n"
            "**Important**: Provide **only** the category name (Bill Audit Form, Invoice, Letter of Guarantee, Medical Report). Do not provide any additional text or explanation.\n\n"
            "Here is the text for classification:\n"
            f"Text: {page_text}\n\n"
            "Provide only the category name."
        )

        # Make a request to the ChatGPT API using the client
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="gpt-4o-mini",
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