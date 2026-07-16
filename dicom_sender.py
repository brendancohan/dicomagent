from typing import List
from pynetdicom import AE
from pydicom.dataset import Dataset
from pynetdicom.sop_class import SecondaryCaptureImageStorage, ModalityWorklistInformationFind, StudyRootQueryRetrieveInformationModelFind
import logging

logger = logging.getLogger("dicom_agent")


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

    logger.info(f"Requesting Association with {pacs_ae_title} at {pacs_ip}:{pacs_port}...")
    assoc = ae.associate(pacs_ip, pacs_port, ae_title=pacs_ae_title)

    if assoc.is_established:
        logger.info("Association established. Sending C-STORE requests...")

        all_success = True
        for idx, ds in enumerate(datasets):
            logger.info(f"Sending dataset {idx + 1} of {len(datasets)}...")
            status = assoc.send_c_store(ds)

            if status:
                logger.info("C-STORE request status: 0x{0:04x}".format(status.Status))
                if status.Status != 0x0000:
                    all_success = False
            else:
                logger.error("Connection timed out, was aborted or received invalid response")
                all_success = False

        # Release the association
        assoc.release()
        return all_success
    else:
        logger.error("Association rejected, aborted or never connected")
        return False


def query_study_uid(
    accession_number: str,
    pacs_ip: str,
    pacs_port: int,
    pacs_ae_title: str,
    agent_ae_title: str,
    is_mwl: bool = False
) -> str:
    """
    Query PACS for StudyInstanceUID given an Accession Number.
    Returns the StudyInstanceUID or None if not found.
    """
    ae = AE(ae_title=agent_ae_title)
    
    sop_class = ModalityWorklistInformationFind if is_mwl else StudyRootQueryRetrieveInformationModelFind
    query_type = "MWL" if is_mwl else "Study Root"
    
    ae.add_requested_context(sop_class)

    logger.info(f"Requesting Association with {pacs_ae_title} at {pacs_ip}:{pacs_port} for C-FIND ({query_type})...")
    assoc = ae.associate(pacs_ip, pacs_port, ae_title=pacs_ae_title)

    if assoc.is_established:
        logger.info(f"Association established. Sending C-FIND request ({query_type})...")

        ds = Dataset()
        if not is_mwl:
            ds.QueryRetrieveLevel = "STUDY"
        ds.AccessionNumber = accession_number
        ds.StudyInstanceUID = ""

        responses = assoc.send_c_find(ds, sop_class)

        study_uid = None
        for (status, identifier) in responses:
            if status:
                # 0xFF00 and 0xFF01 are 'Pending' statuses (which means matches)
                if status.Status in (0xFF00, 0xFF01) and identifier:
                    if 'StudyInstanceUID' in identifier:
                        study_uid = identifier.StudyInstanceUID
                        logger.info(f"C-FIND match found in {query_type}! Extracted StudyInstanceUID: {study_uid}")
                        break # We just need the first match
            else:
                logger.error(f"Connection timed out, was aborted or received invalid response during C-FIND ({query_type})")

        assoc.release()
        return study_uid
    else:
        logger.error(f"Association rejected, aborted or never connected for C-FIND ({query_type})")
        return None
