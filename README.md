# DICOM Agent Service

A lightweight, cross-platform microservice built with Python and FastAPI that encapsulates PDF documents into standard pixel-data DICOM Secondary Capture images and transmits them to a target PACS (Picture Archiving and Communication System) using the DICOM standard (C-STORE).

## Features

- **REST API to DICOM Bridge**: Easily connect external applications (like Power Apps, web portals, or EHRs) to your PACS via simple HTTP POST requests.
- **PDF to Pixel Data**: Automatically renders all pages of an uploaded PDF into high-quality RGB images and creates `Secondary Capture Image Storage` DICOM files.
- **Multi-page Support**: A single multi-page PDF becomes a sequence of DICOM instances in the same Study/Series.
- **Dynamic Configuration UI**: Update the target PACS IP, Port, and AE Titles via a built-in web dashboard without restarting the service.
- **OpenAPI Ready**: Native Swagger/OpenAPI support makes it 1-click simple to generate "Custom Connectors" for Microsoft Power Apps and Power Automate.

## Requirements

- Python 3.10+

## Installation

### Linux / macOS

1. Run the installation script:
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

### Windows

1. Double-click `install.bat`, or run it from the command prompt:
   ```cmd
   install.bat
   ```

## Starting the Service

### Linux / macOS
```bash
source venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

### Windows
```cmd
venv\Scripts\activate
uvicorn main:app --host 0.0.0.0 --port 8000
```

## Configuration

You can configure the service dynamically via the built-in UI:

1. Open your browser and navigate to: `http://localhost:8000/config-ui`
2. Update the target parameters:
   - **PACS IP**: The IP address or hostname of your target PACS server.
   - **PACS Port**: The DICOM listener port (commonly 104 or 11112).
   - **PACS AE Title**: The Application Entity Title of the PACS.
   - **Agent AE Title**: The Application Entity Title this service will use when sending files.
3. Click "Save Configuration". The service will instantly use these settings on the next request.

*(Alternatively, you can manually create/edit the `.env` file in the root directory).*

## API Usage

The main endpoint is `POST /api/v1/dicom/encapsulate-pdf`. It accepts a `multipart/form-data` payload.

### Request Parameters (Form Data)

| Field | Type | Description | Required |
|---|---|---|---|
| `pdf_file` | File | The PDF file to upload (`application/pdf`) | Yes |
| `patient_id` | Text | Unique identifier for the patient | Yes |
| `patient_name` | Text | The patient's name (e.g. `Doe^John`) | Yes |
| `accession_number`| Text | Order/Accession number for the study | No |
| `dob` | Text | Patient Date of Birth (`YYYYMMDD`) | No |
| `sex` | Text | Patient Sex (`M`, `F`, or `O`) | No |

### Example Request (cURL)

```bash
curl -X POST "http://localhost:8000/api/v1/dicom/encapsulate-pdf" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "pdf_file=@/path/to/document.pdf;type=application/pdf" \
  -F "patient_id=12345" \
  -F "patient_name=Smith^Jane" \
  -F "accession_number=ACC999" \
  -F "dob=19850101" \
  -F "sex=F"
```

## Documentation & Power Apps Integration

The complete Swagger (OpenAPI) documentation is automatically hosted at:
- **`http://localhost:8000/docs`**

To integrate with Microsoft Power Apps:
1. Go to `http://localhost:8000/openapi.json` and save the output as a `.json` file.
2. In Power Apps or Power Automate, go to **Custom Connectors** -> **New custom connector** -> **Import an OpenAPI file**.
3. Upload the JSON file. Power Apps will automatically map the API parameters and create a ready-to-use Connector for your workflows!

## Logging

All transaction attempts and system errors are logged to `dicom_agent.log` located in the root directory.
