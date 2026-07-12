from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from pydantic import BaseModel
from dotenv import load_dotenv, set_key
import os
import logging

from logging.handlers import TimedRotatingFileHandler

log_formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Rotate daily at midnight, keep 7 days of logs
file_handler = TimedRotatingFileHandler(
    filename="dicom_agent.log",
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)
file_handler.setFormatter(log_formatter)

console_handler = logging.StreamHandler()
console_handler.setFormatter(log_formatter)

# Configure the root logger to capture all logs (including pynetdicom and uvicorn)
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(file_handler)
root_logger.addHandler(console_handler)

logger = logging.getLogger("dicom_agent")

from dicom_converter import convert_pdf_to_dicom
from dicom_sender import send_dicom_to_pacs, query_study_uid

ENV_FILE = ".env"
load_dotenv(ENV_FILE)

app = FastAPI(
    title="DICOM Agent Service",
    description="API to encapsulate PDFs into DICOM and send to PACS",
    version="1.0.0",
)


class Config(BaseModel):
    pacs_ip: str
    pacs_port: int
    pacs_ae_title: str
    agent_ae_title: str


def get_current_config() -> Config:
    load_dotenv(ENV_FILE, override=True)
    return Config(
        pacs_ip=os.getenv("PACS_IP", "www.dicomserver.co.uk"),
        pacs_port=int(os.getenv("PACS_PORT", "11112")),
        pacs_ae_title=os.getenv("PACS_AE_TITLE", "MOCK_PACS"),
        agent_ae_title=os.getenv("AGENT_AE_TITLE", "MY_AGENT"),
    )


@app.get("/api/v1/config", response_model=Config, summary="Get current configuration")
def get_config():
    return get_current_config()


@app.post("/api/v1/config", summary="Update configuration")
def update_config(config: Config):
    if not os.path.exists(ENV_FILE):
        open(ENV_FILE, "w").close()

    set_key(ENV_FILE, "PACS_IP", config.pacs_ip)
    set_key(ENV_FILE, "PACS_PORT", str(config.pacs_port))
    set_key(ENV_FILE, "PACS_AE_TITLE", config.pacs_ae_title)
    set_key(ENV_FILE, "AGENT_AE_TITLE", config.agent_ae_title)
    return {"message": "Configuration updated successfully"}


@app.get(
    "/config-ui", response_class=HTMLResponse, summary="Simple UI for configuration"
)
def config_ui():
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>DICOM Agent Configuration</title>
        <style>
            body { font-family: sans-serif; margin: 40px; background-color: #f4f7f6; }
            .container { max-width: 500px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h2 { margin-top: 0; color: #333; }
            .form-group { margin-bottom: 15px; }
            label { display: block; margin-bottom: 5px; font-weight: bold; color: #555; }
            input[type="text"], input[type="number"] { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
            button { width: 100%; padding: 10px 15px; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; }
            button:hover { background-color: #0056b3; }
            #message { margin-top: 15px; font-weight: bold; text-align: center; height: 20px; }
            .success { color: green; }
            .error { color: red; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>DICOM Agent Configuration</h2>
            <div class="form-group">
                <label>PACS IP / Hostname</label>
                <input type="text" id="pacs_ip" />
            </div>
            <div class="form-group">
                <label>PACS Port</label>
                <input type="number" id="pacs_port" />
            </div>
            <div class="form-group">
                <label>PACS AE Title</label>
                <input type="text" id="pacs_ae_title" />
            </div>
            <div class="form-group">
                <label>Agent AE Title (Our AE Title)</label>
                <input type="text" id="agent_ae_title" />
            </div>
            <button onclick="saveConfig()">Save Configuration</button>
            <div id="message"></div>
        </div>

        <script>
            async function loadConfig() {
                try {
                    const response = await fetch('/api/v1/config');
                    const data = await response.json();
                    document.getElementById('pacs_ip').value = data.pacs_ip;
                    document.getElementById('pacs_port').value = data.pacs_port;
                    document.getElementById('pacs_ae_title').value = data.pacs_ae_title;
                    document.getElementById('agent_ae_title').value = data.agent_ae_title;
                } catch (e) {
                    showMessage("Failed to load configuration", false);
                }
            }

            async function saveConfig() {
                const config = {
                    pacs_ip: document.getElementById('pacs_ip').value,
                    pacs_port: parseInt(document.getElementById('pacs_port').value),
                    pacs_ae_title: document.getElementById('pacs_ae_title').value,
                    agent_ae_title: document.getElementById('agent_ae_title').value
                };

                try {
                    const response = await fetch('/api/v1/config', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(config)
                    });
                    
                    if (response.ok) {
                        showMessage("Configuration saved successfully!", true);
                    } else {
                        showMessage("Failed to save configuration", false);
                    }
                } catch (e) {
                    showMessage("Error saving configuration", false);
                }
            }

            function showMessage(msg, isSuccess) {
                const el = document.getElementById('message');
                el.textContent = msg;
                el.className = isSuccess ? 'success' : 'error';
                setTimeout(() => el.textContent = '', 3000);
            }

            window.onload = loadConfig;
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.post(
    "/api/v1/dicom/encapsulate-pdf", summary="Convert PDF to DICOM and send to PACS"
)
async def encapsulate_and_send_pdf(
    pdf_file: UploadFile = File(..., description="The PDF file to be converted"),
    patient_id: str = Form(..., description="The ID of the patient"),
    patient_name: str = Form(
        ..., description="The name of the patient (e.g., Doe^John)"
    ),
    accession_number: str = Form("", description="The Accession Number for the study"),
    dob: str = Form("", description="Patient Date of Birth (YYYYMMDD)"),
    sex: str = Form("", description="Patient Sex (M, F, O)"),
    series_description: str = Form("Ref Document", description="Description of the DICOM series"),
):
    if pdf_file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Uploaded file must be a PDF")

    try:
        # Read current config for each request
        config = get_current_config()
        
        logger.info(f"Received PDF encapsulation request. File: '{pdf_file.filename}', Accession: '{accession_number}', PatientID: '{patient_id}'")

        if not accession_number:
            raise HTTPException(status_code=400, detail="Accession Number is required to query PACS for StudyUID")

        # Query PACS for the StudyInstanceUID
        study_uid = query_study_uid(
            accession_number=accession_number,
            pacs_ip=config.pacs_ip,
            pacs_port=config.pacs_port,
            pacs_ae_title=config.pacs_ae_title,
            agent_ae_title=config.agent_ae_title,
        )

        if not study_uid:
            raise HTTPException(
                status_code=404,
                detail=f"Study not found in PACS for Accession Number: {accession_number}"
            )

        logger.info(f"Successfully retrieved StudyInstanceUID: {study_uid} from PACS for Accession: {accession_number}")

        # Read the PDF bytes
        pdf_bytes = await pdf_file.read()

        # 1. Convert to DICOM
        dicom_datasets = convert_pdf_to_dicom(
            pdf_bytes=pdf_bytes,
            patient_id=patient_id,
            patient_name=patient_name,
            accession_number=accession_number,
            dob=dob,
            sex=sex,
            series_description=series_description,
            study_instance_uid=study_uid,
        )

        # 2. Send to PACS
        success = send_dicom_to_pacs(
            datasets=dicom_datasets,
            pacs_ip=config.pacs_ip,
            pacs_port=config.pacs_port,
            pacs_ae_title=config.pacs_ae_title,
            agent_ae_title=config.agent_ae_title,
        )

        if success:
            return JSONResponse(
                status_code=200,
                content={"message": "DICOM file successfully created and sent to PACS"},
            )
        else:
            raise HTTPException(
                status_code=502,
                detail="Failed to send DICOM file to PACS. Check connection or PACS logs.",
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
