## Installation
1. First, make sure you have Python installed on your system. You can download it from [here](https://www.python.org/downloads/).
2. Clone this repository to your local machine.
3. Navigate to the project directory in your terminal.
4. Create a virtual environment using the following command:
python -m venv venv

5. Activate the virtual environment:
- On Windows:
  ```
  venv\Scripts\activate
  ```

6. Install the required packages using pip:
pip install -r requirements.txt

7. Download and install Tesseract OCR from [here](https://digi.bib.uni-mannheim.de/tesseract/tesseract-ocr-w64-setup-5.3.4.20240503.exe). Install it to `C:/Program Files/Tesseract-OCR/tesseract`.
8. Open `app.py` and navigate to line 7.
9. Change the import statements from:
```
from werkzeug import secure_filename, FileStorage
```
to:
```
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
```
Run the application:
python app.py
