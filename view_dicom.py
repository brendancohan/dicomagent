import os
import pydicom
import matplotlib.pyplot as plt
import numpy as np


def view_dicom(file_path):
    # Load the DICOM file
    ds = pydicom.dcmread(file_path)

    # Get the pixel array
    pixel_array = ds.pixel_array

    # Check if it's RGB
    if ds.PhotometricInterpretation == "RGB":
        plt.imshow(pixel_array)
    else:
        plt.imshow(pixel_array, cmap="gray")

    plt.title(f"Page {ds.InstanceNumber} - {os.path.basename(file_path)}")
    plt.axis("off")
    plt.show()


if __name__ == "__main__":
    downloads_dir = os.path.expanduser("~/Downloads")

    for i in range(1, 4):
        file_path = os.path.join(downloads_dir, f"output_page_{i}.dcm")
        if os.path.exists(file_path):
            print(f"Opening {file_path}...")
            view_dicom(file_path)
