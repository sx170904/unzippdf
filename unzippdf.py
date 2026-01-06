import streamlit as st
import zipfile
import io
import os
import re
from pypdf import PdfWriter

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', s)]

def process_nested_zips(uploaded_file):
    output_zip_buffer = io.BytesIO()
    log_report = [] # To keep track of what happened
    
    with zipfile.ZipFile(uploaded_file, 'r') as outer_zip:
        with zipfile.ZipFile(output_zip_buffer, "w", zipfile.ZIP_DEFLATED) as new_outer_zip:
            
            all_files = sorted(outer_zip.namelist(), key=natural_sort_key)
            combination_count = 1
            
            for name in all_files:
                if "__MACOSX" in name or ".DS_Store" in name:
                    continue

                if name.endswith('.zip'):
                    with outer_zip.open(name) as nested_zip_data:
                        nested_zip_buffer = io.BytesIO(nested_zip_data.read())
                        
                        try:
                            with zipfile.ZipFile(nested_zip_buffer, 'r') as inner_zip:
                                merger = PdfWriter()
                                pdf_found = False
                                files_merged_here = []
                                
                                # Strictly look ONLY inside THIS specific inner_zip
                                inner_files = sorted(inner_zip.namelist(), key=natural_sort_key)
                                for inner_file in inner_files:
                                    if inner_file.endswith('.pdf'):
                                        with inner_zip.open(inner_file) as pdf_file:
                                            merger.append(io.BytesIO(pdf_file.read()))
                                            pdf_found = True
                                            files_merged_here.append(inner_file)
                                
                                if pdf_found:
                                    combined_pdf_buffer = io.BytesIO()
                                    merger.write(combined_pdf_buffer)
                                    merger.close()
                                    
                                    new_filename = f"combined {combination_count}.pdf"
                                    folder_path = os.path.dirname(name)
                                    final_path = os.path.join(folder_path, new_filename)
                                    
                                    new_outer_zip.writestr(final_path, combined_pdf_buffer.getvalue())
                                    
                                    # Add to log for user verification
                                    log_report.append(f"SUCCESS: Created '{final_path}' using {files_merged_here} from {name}")
                                    combination_count += 1
                        except Exception as e:
                            log_report.append(f"ERROR: Could not process {name} - {str(e)}")
                
                elif not name.endswith('/') and not name.endswith('.zip'):
                    with outer_zip.open(name) as file_data:
                        new_outer_zip.writestr(name, file_data.read())

            # Create a summary text file inside the zip for the user to check
            summary_content = "\n".join(log_report)
            new_outer_zip.writestr("processing_summary.txt", summary_content)

    return output_zip_buffer.getvalue(), log_report

# --- Streamlit UI ---
st.set_page_config(page_title="Secure PDF Merger")
st.title("📂 Verified PDF Merger")

uploaded_file = st.file_uploader("Upload Zip", type="zip")

if uploaded_file and st.button("Start Processing"):
    with st.spinner("Merging..."):
        processed_data, logs = process_nested_zips(uploaded_file)
        
        st.success("Task Finished!")
        
        # Display the logs in the app so you can see it worked
        with st.expander("View Processing Log"):
            for line in logs:
                st.text(line)
        
        st.download_button("Download Result (Includes Summary Log)", processed_data, "merged_result.zip")