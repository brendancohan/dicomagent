import sys
import pydicom


def extract_pdf_from_dicom(dicom_file_path: str, output_pdf_path: str):
    """Reads a DICOM file and extracts the embedded PDF."""
    ds = pydicom.dcmread(dicom_file_path)
    if "EncapsulatedDocument" not in ds:
        print(f"Error: {dicom_file_path} does not contain an EncapsulatedDocument tag.")
        sys.exit(1)

    if ds.MIMETypeOfEncapsulatedDocument != "application/pdf":
        print("Warning: MIME type is not application/pdf.")

    pdf_bytes = ds.EncapsulatedDocument

    # Strip the trailing null byte if it was added for padding
    if pdf_bytes.endswith(b"\x00"):
        pdf_bytes = pdf_bytes[:-1]

    with open(output_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Successfully extracted PDF to {output_pdf_path}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python extract_pdf.py <input.dcm> <output.pdf>")
        sys.exit(1)
    extract_pdf_from_dicom(sys.argv[1], sys.argv[2])
