import os
import pydicom
from dicom_converter import convert_pdf_to_dicom


def process_and_save(pdf_path, output_dir):
    with open(pdf_path, "rb") as f:
        pdf_bytes = f.read()

    # Convert to DICOM datasets
    datasets = convert_pdf_to_dicom(
        pdf_bytes=pdf_bytes,
        patient_id="TEST-LOCAL-1",
        patient_name="Local^Test",
        accession_number="ACC-LOCAL",
        dob="20000101",
        sex="O",
    )

    print(f"Generated {len(datasets)} DICOM files from {pdf_path}")

    # Save each dataset as a .dcm file in the output directory
    for i, ds in enumerate(datasets):
        output_filename = f"output_page_{i + 1}.dcm"
        output_path = os.path.join(output_dir, output_filename)
        pydicom.filewriter.dcmwrite(output_path, ds)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    downloads_dir = os.path.expanduser("~/Downloads")
    pdf_path = os.path.join(downloads_dir, "sample-local-pdf.pdf")

    if not os.path.exists(pdf_path):
        print(f"Error: Could not find {pdf_path}")
    else:
        process_and_save(pdf_path, downloads_dir)
