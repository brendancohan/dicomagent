import datetime
from typing import List
import pydicom
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import generate_uid, UID, ExplicitVRLittleEndian
import fitz  # PyMuPDF


def convert_pdf_to_dicom(
    pdf_bytes: bytes,
    patient_id: str,
    patient_name: str,
    accession_number: str = "",
    dob: str = "",
    sex: str = "",
    series_description: str = "Ref Document",
    study_instance_uid: str = None,
) -> List[pydicom.Dataset]:
    """
    Renders PDF pages to images and creates a list of Secondary Capture DICOM datasets.
    """

    datasets = []

    # Open the PDF from bytes
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    # Generate common UIDs for the entire study/series
    if not study_instance_uid:
        study_instance_uid = generate_uid()
    series_instance_uid = generate_uid()

    # Standard Date and Time
    dt = datetime.datetime.now()
    creation_date = dt.strftime("%Y%m%d")
    creation_time = dt.strftime("%H%M%S.%f")

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Render the page to an RGB image (zoom by 2 for better resolution)
        matrix = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=matrix, alpha=False)

        # The pixel data as RGB bytes
        pixel_bytes = pix.samples

        # Secondary Capture Image Storage
        sop_class_uid = UID("1.2.840.10008.5.1.4.1.1.7")
        sop_instance_uid = generate_uid()

        file_meta = FileMetaDataset()
        file_meta.MediaStorageSOPClassUID = sop_class_uid
        file_meta.MediaStorageSOPInstanceUID = sop_instance_uid
        file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        file_meta.ImplementationClassUID = generate_uid()

        ds = FileDataset("", {}, file_meta=file_meta, preamble=b"\0" * 128)

        ds.InstanceCreationDate = creation_date
        ds.InstanceCreationTime = creation_time

        # --- DICOM Dataset Header (Metadata) ---
        ds.SOPClassUID = file_meta.MediaStorageSOPClassUID
        ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID

        # Patient Module
        ds.PatientName = patient_name
        ds.PatientID = patient_id
        ds.PatientBirthDate = dob
        ds.PatientSex = sex

        # Study Module
        ds.StudyInstanceUID = study_instance_uid
        ds.StudyDate = creation_date
        ds.StudyTime = creation_time
        ds.AccessionNumber = accession_number
        ds.ReferringPhysicianName = ""
        ds.StudyID = "1"

        # Series Module
        ds.SeriesInstanceUID = series_instance_uid
        ds.SeriesNumber = 1
        ds.Modality = "OT"  # Other
        if series_description:
            ds.SeriesDescription = series_description

        # Equipment Module
        ds.Manufacturer = "DICOM Agent Service"
        ds.ConversionType = "WSD"  # Workstation

        # General Image Module
        ds.InstanceNumber = page_num + 1

        # --- Pixel Data ---
        ds.SamplesPerPixel = 3
        ds.PhotometricInterpretation = "RGB"
        ds.PlanarConfiguration = 0
        ds.NumberOfFrames = 1
        ds.Rows = pix.height
        ds.Columns = pix.width
        ds.BitsAllocated = 8
        ds.BitsStored = 8
        ds.HighBit = 7
        ds.PixelRepresentation = 0

        # Pixel data length must be even
        if len(pixel_bytes) % 2 != 0:
            pixel_bytes += b"\0"

        ds.PixelData = pixel_bytes

        datasets.append(ds)

    doc.close()
    return datasets
