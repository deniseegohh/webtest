import os 
from flask import Flask, json, render_template, request, redirect, flash
import requests
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from google import genai
import markdown
import time

## load environment variables
load_dotenv()
VIRUSTOTAL_API_KEY = os.getenv("VIRUSTOTAL_API_KEY")
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'jpg', 'png', 'exe', 'js'}
MAX_CONTENT_LENGTH = 16 * 1024 * 1024
client = genai.Client()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.secret_key = "supersecretkey"

def check_allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def scan_file_virustotal(filepath):
    url = "https://www.virustotal.com/api/v3/files"
    headers = {
        "x-apikey": VIRUSTOTAL_API_KEY,
        "accept": "application/json"
    }
    with open(filepath, "rb") as f:
        files = {"file": (os.path.basename(filepath), f)}
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        time.sleep(2)
        result = response.json()
        analysis_id = result["data"]["id"]
        for _ in range(10):
            response = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers)
            if response.status_code == 200 and response.json()['data']['attributes']['status'] == "completed":
                return response.json()['data']['attributes']['results']
            time.sleep(3)
    return {"error": "Scan failed or timed out"}

def explain_scan_results(scan_result):
    result_string = "\n".join([f"{engine}: {data["category"]}" for engine, data in scan_result.items()])

    prompt = f"Summarise the following antivirus scan results in a short, structured format with bullet points for: \n Overall verdict \n Key findings (if any) \n What the user should do next \n Keep the total under 100 words and use simple language. \n Antivirus scan results: \n{result_string}"
    response = client.models.generate_content(
        model="gemini-2.5-flash", 
        contents=prompt
    )

    return response.text

@app.route('/', methods=['GET', 'POST'])
def index():

    if request.method == 'POST':
        ## check if POST request actually has a file
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']

        ## check if user actually selected a file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and check_allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            scan_result = scan_file_virustotal(filepath)
            os.remove(filepath)
            return render_template('index.html', result=scan_result, filename=filename)

    return render_template('index.html')

@app.route('/explain', methods=['POST'])
def explain():
    scan_result = request.form.get('scan_result')

    if not scan_result:
        return {'error': 'No scan result provided'}, 400
    
    scan_result = json.loads(scan_result)
    ai_explanation = explain_scan_results(scan_result)
    ai_explanation_html = markdown.markdown(ai_explanation)
    return {'ai_text': ai_explanation_html}

if __name__ == "__main__":
    app.run(debug=True)