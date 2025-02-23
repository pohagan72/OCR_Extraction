**100% of this app was written using Generative AI, including this Readme file**

# OCR Extraction Application

This repository contains a Flask-based web application that uses the **Azure OCR Service** to extract text from images and generate a downloadable Excel report containing the extracted text. The application is designed for batch processing and supports a variety of image formats, with a focus on scalability and usability.

---

## Key Features

- **Batch OCR Processing**: Process all images in a folder in one go.
- **Azure OCR Integration**: Leverages the Azure OCR service for accurate text extraction.
- **Excel Report Generation**: Outputs extracted text into a downloadable `.xlsx` file.
- **File Format Handling**: Automatically converts unsupported image formats to supported formats (e.g., PNG, JPG).
- **Real-Time Progress Tracking**: Provides progress updates during processing.
- **Web-Based Interface**: User-friendly HTML interface for inputting folder paths and tracking progress.
- **Retry Logic**: Automatically retries failed OCR calls with exponential back-off to ensure robustness.
- **Scalable Design**: Processes images concurrently using a thread pool for improved performance.

---

## Screenshot

![OCR Processor Screenshot](https://github.com/user-attachments/assets/a7509103-0ec8-43ad-86cc-204894f45e24)

---

## How to Set Up and Run

### Prerequisites

1. **Python**: Ensure Python 3.8 or later is installed.
2. **Azure Credentials**: You need an Azure Cognitive Services account with a valid **Endpoint** and **API Key**.
3. **Libraries**: Install the required Python packages listed in `requirements.txt` (or below).

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/OCR_Extraction.git
   cd OCR_Extraction
