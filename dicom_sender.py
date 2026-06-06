from typing import List
from pynetdicom import AE
from pydicom.dataset import Dataset
from pynetdicom.sop_class import SecondaryCaptureImageStorage


def send_dicom_to_pacs(
    datasets: List[Dataset],
    pacs_ip: str,
    pacs_port: int,
    pacs_ae_title: str,
    agent_ae_title: str,
) -> bool:
    """
    Acts as a DICOM SCU to send multiple datasets to a PACS via C-STORE.
    Returns True if all successful, False otherwise.
    """

    # Initialize the Application Entity
    ae = AE(ae_title=agent_ae_title)

    # We are sending Secondary Capture Images
    ae.add_requested_context(SecondaryCaptureImageStorage)

    print(f"Requesting Association with {pacs_ae_title} at {pacs_ip}:{pacs_port}...")
    assoc = ae.associate(pacs_ip, pacs_port, ae_title=pacs_ae_title)

    if assoc.is_established:
        print("Association established. Sending C-STORE requests...")

        all_success = True
        for idx, ds in enumerate(datasets):
            print(f"Sending dataset {idx + 1} of {len(datasets)}...")
            status = assoc.send_c_store(ds)

            if status:
                print("C-STORE request status: 0x{0:04x}".format(status.Status))
                if status.Status != 0x0000:
                    all_success = False
            else:
                print("Connection timed out, was aborted or received invalid response")
                all_success = False

        # Release the association
        assoc.release()
        return all_success
    else:
        print("Association rejected, aborted or never connected")
        return False
