import streamlit as st
import zipfile
import io
import os
from pypdf import PdfWriter

def process_nested_zips(uploaded_file):
    # Create an in-memory buffer for the final output zip
    output_zip_buffer = io.BytesIO()
    
    with zipfile.ZipFile(uploaded_file, 'r') as outer_zip:
        # Create the new zip file we will eventually let the user download
        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as new_outer_zip:
            
            # List all members in the uploaded zip
            outer_names = outer_zip.namelist()
            
            # Track how many times we've combined PDFs for naming
            combination_count = 1
            
            # We process files folder by folder
            for name in outer_names:
                # If the file is a nested zip
                if name.endswith('.zip'):
                    # Open the nested zip file
                    with outer_zip.open(name) as nested_zip_data:
                        nested_zip_buffer = io.BytesIO(nested_zip_data.read())
                        
                        with zipfile.ZipFile(nested_zip_buffer, 'r') as inner_zip:
                            merger = PdfWriter()
                            pdf_found = False
                            
                            # Find and append all PDFs inside the inner zip
                            for inner_file in sorted(inner_zip.namelist()):
                                if inner_file.endswith('.pdf'):
                                    with inner_zip.open(inner_file) as pdf_file:
                                        merger.append(io.BytesIO(pdf_file.read()))
                                        pdf_found = True
                            
                            if pdf_found:
                                # Create the combined PDF in memory
                                combined_pdf_buffer = io.BytesIO()
                                merger.write(combined_pdf_buffer)
                                merger.close()
                                
                                # Name it: combined 1.pdf, combined 2.pdf, etc.
                                new_filename = f"combined {combination_count}.pdf"
                                # Add to the new outer zip (placing it in the same relative path)
                                folder_path = os.path.dirname(name)
                                new_outer_zip.writestr(os.path.join(folder_path, new_filename), combined_pdf_buffer.getvalue())
                                
                                combination_count += 1
                else:
                    # If it's just a regular file (not a zip), keep it as is
                    with outer_zip.open(name) as file_data:
                        new_outer_zip.writestr(name, file_data.read())

    return output_zip_buffer.getvalue()

# --- Streamlit UI ---
st.title("📂 PDF Zip Merger")
st.write("Upload a zip containing folders with nested zips to merge PDFs.")

uploaded_file = st.file_uploader("Choose a Zip file", type="zip")

if uploaded_file:
    with st.spinner("Processing files..."):
        try:
            processed_data = process_nested_zips(uploaded_file)
            
            st.success("Task completed successfully!")
            st.download_button(
                label="Download Processed Zip",
                data=processed_data,
                file_name="processed_files.zip",
                mime="application/zip"
            )
        except Exception as e:
            st.error(f"An error occurred: {e}")