from ocr import generate_ocr_files
from pdf_splitting import process_all_pdfs_in_folder
from document_translator import process_and_combine
from combine_extracted_csv import combine_csv_files
from datetime import datetime

input_dir = 'test'
output_dir = 'test_output'
ocr_output_dir = f'{output_dir}/ocr_files'
split_pdf_dir = f'{output_dir}/split_pdfs'
extracted_csv_dir = f'{output_dir}/extracted_csv'

def main():
    start_time = datetime.now()
    
    generate_ocr_files(input_dir, ocr_output_dir)
    process_all_pdfs_in_folder(ocr_output_dir, split_pdf_dir)
    process_and_combine(split_pdf_dir, extracted_csv_dir)
    print(f"Processed data saved to {extracted_csv_dir}")
    combine_csv_files(extracted_csv_dir, extracted_csv_dir)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    end_time = datetime.now()
    print(f"End time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    elapsed_time = end_time - start_time
    print(f"Elapsed time: {elapsed_time}")


if __name__ == '__main__':
    main()