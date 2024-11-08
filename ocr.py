import logging
import sys
import os
import subprocess
from ctypes.util import find_library
find_library("gs")

file_list = []

input_folder_path = ''
output_folder_path = ''

input_folder_path = os.path.join(os.getcwd(), 'old_invoice')
for filename in os.listdir(input_folder_path):
    if filename.endswith("pdf"):
      file_list.append(filename)


for filename in file_list:
    print("Converting:", filename)
    input_filename = os.path.join(input_folder_path, filename)
    output_filename = os.path.join(output_folder_path, filename.replace(".pdf", "_ocr.pdf"))

    # Use subprocess to call ocrmypdf
    try:
        subprocess.run(
            ["ocrmypdf", "--deskew", "--force-ocr", input_filename, output_filename],
            check=True
        )
        print(f"Successfully processed: {filename}")
    except subprocess.CalledProcessError as e:
        print(f"Error processing {filename}: {e}")
    