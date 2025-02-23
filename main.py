import os
import time
import logging
import io
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from PIL import Image
from azure.cognitiveservices.vision.computervision import ComputerVisionClient
from azure.cognitiveservices.vision.computervision.models import OperationStatusCodes
from msrest.authentication import CognitiveServicesCredentials
import openpyxl
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock
from tenacity import retry, stop_after_attempt, wait_exponential

# Flask app setup
app = Flask(__name__)

# Configure logging
logging.basicConfig(filename='ocr_processing.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Hardcoded Azure credentials (not recommended for production)
AZURE_ENDPOINT = "Endpoint_Goes_Here"
AZURE_KEY = "Key_Goes_Here"

# Initialize Azure Computer Vision client
computervision_client = ComputerVisionClient(AZURE_ENDPOINT, CognitiveServicesCredentials(AZURE_KEY))

# Supported image extensions
SUPPORTED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "tiff"}

# Global variables for tracking progress
total_images = 0
processed_images = 0
start_time = None
results_lock = Lock()
results = []
is_processing = False  # Track if processing has started

# Function to check if a file is an image
def is_image_file(file_path):
    return file_path.lower().endswith(tuple(SUPPORTED_EXTENSIONS))

# Function to convert unsupported images to a supported format (e.g., JPG)
def convert_to_supported_format(file_path):
    try:
        img = Image.open(file_path)
        rgb_img = img.convert("RGB")
        base_name = os.path.splitext(file_path)[0]
        new_file_path = f"{base_name}.jpg"
        rgb_img.save(new_file_path, "JPEG")
        return new_file_path
    except Exception as e:
        logging.error(f"Error converting file {file_path}: {str(e)}")
        return None

# Retry logic for Azure API calls
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def perform_ocr(file_path):
    global processed_images
    try:
        if not is_image_file(file_path):
            converted_file_path = convert_to_supported_format(file_path)
            if converted_file_path:
                file_path = converted_file_path
            else:
                logging.error(f"Unsupported file format: {file_path}")
                return

        with open(file_path, "rb") as image_file:
            image_data = image_file.read()

        image_stream = io.BytesIO(image_data)
        response = computervision_client.read_in_stream(image_stream, raw=True)
        operation_id = response.headers["Operation-Location"].split("/")[-1]

        while True:
            result = computervision_client.get_read_result(operation_id)
            if result.status not in [OperationStatusCodes.running, OperationStatusCodes.not_started]:
                break
            time.sleep(1)

        extracted_text = ""
        if result.status == OperationStatusCodes.succeeded:
            for page in result.analyze_result.read_results:
                for line in page.lines:
                    extracted_text += line.text + "\n"

        with results_lock:
            results.append((os.path.basename(file_path), extracted_text.strip()))
    except Exception as e:
        logging.error(f"Failed to process {file_path}: {str(e)}")
    finally:
        with results_lock:
            processed_images += 1
            app.logger.info(f"Processed {processed_images}/{total_images} images")

# Function to process all images in a folder
def process_folder(folder_path):
    global total_images, start_time, results, is_processing

    results = []
    if not os.path.isdir(folder_path):
        return jsonify({"error": "Invalid folder path"}), 400

    image_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if is_image_file(f)]
    total_images = len(image_files)
    start_time = time.time()
    is_processing = True  # Set processing state to True

    # Create a temporary file to store the Excel results
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp_file:
        output_file = tmp_file.name
        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = "OCR Results"
        sheet.append(["File Name", "Extracted Text"])

        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(perform_ocr, file_path) for file_path in image_files]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logging.error(f"Error processing image: {str(e)}")

        # Append results to Excel file incrementally
        for name, text in results:
            sheet.append([name, text])
        workbook.save(output_file)

    is_processing = False  # Set processing state to False after completion

    # Return the Excel file as a downloadable response
    return send_file(
        output_file,
        as_attachment=True,
        download_name="ocr_results.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Flask routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/process", methods=["POST"])
def start_processing():
    folder_path = request.json.get("folder_path")
    if not folder_path:
        return jsonify({"error": "Folder path is required"}), 400
    return process_folder(folder_path)

@app.route("/progress")
def get_progress():
    global total_images, processed_images, is_processing
    if not is_processing:
        return jsonify({
            "total_images": 0,
            "processed_images": 0
        })
    return jsonify({
        "total_images": total_images,
        "processed_images": processed_images
    })

if __name__ == "__main__":
    app.run(debug=False)
