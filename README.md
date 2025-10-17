# 🛡️ SecureScan — File Malware Analysis with VirusTotal & Gemini AI

**SecureScan** is a cloud-based web application that scans uploaded files using the **VirusTotal API** and generates a plain-language explanation of the results using **Google Gemini**.  
It is built with **Python (Flask)** and deployed on **AWS EC2** using **Gunicorn**.

---

## Quick Start

### Local Development

```bash
# Clone and setup
git clone https://github.com/deniseegohh/webtest.git
cd webtest
python3 -m venv venv
source venv/bin/activate

# Install and run
pip install -r requirements.txt
python app.py
```

Visit: `http://localhost:5000`

### Production (AWS EC2)

```bash
nohup gunicorn -w 2 --timeout 300 -b 0.0.0.0:8000 app:app > gunicorn.log 2>&1 &
```

Access: `http://3.27.10.229:8000/`

---

## Setup Process

### 1. Environment Variables

Create `.env` file with your API keys:

```env
VIRUSTOTAL_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
SECRET_KEY=your-secret-key
```

Get keys:
- VirusTotal: https://www.virustotal.com (free tier: 500 requests/day)
- Gemini: https://ai.google.dev (free tier available)

### 2. AWS EC2 Setup

Launch instance:
- **AMI**: Amazon Linux 2023 or Ubuntu 20.04 LTS
- **Type**: t3.micro (free tier)
- **Security**: Open ports 22 (SSH), 80 (HTTP), 8000 (app)

Connect and install:
```bash
ssh -i your-key.pem ec2-user@your-ip

# Amazon Linux
sudo dnf install -y python3.11 python3.11-pip git

# Ubuntu
sudo apt install -y python3-pip python3-venv git
```

Deploy:
```bash
git clone https://github.com/deniseegohh/webtest.git
cd webtest
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
nano .env  # Add your API keys
mkdir -p uploads

nohup gunicorn -w 2 --timeout 300 -b 0.0.0.0:8000 app:app > gunicorn.log 2>&1 &
```

### 3. Verify Installation

```bash
# Local
python app.py

# EC2
ps aux | grep gunicorn
tail -f gunicorn.log
```

---


### Challenge : VirusTotal Scan Timeout

**Problem:**
Scans take 2-3 minutes, but Gunicorn's default 120-second timeout was killing the request. Users saw "500 Internal Server Error" after 30 seconds. Refreshing the page showed results (scan had completed in the background).

**Root Cause:**
Gunicorn terminated worker processes when requests exceeded timeout, interrupting the polling loop before scan completion.

**Solution:**
Increased Gunicorn timeout to 300 seconds:

```bash
# Before
gunicorn -w 2 --timeout 120 -b 0.0.0.0:8000 app:app

# After
gunicorn -w 2 --timeout 300 -b 0.0.0.0:8000 app:app
```

300 seconds covers:
- File upload: 0-30 seconds
- VirusTotal analysis: 30 seconds to 3 minutes
- Safety margin: 1-2 minutes

---

## Project Structure

```
securescan/
├── README.md                 # This file
├── .env                      # API keys (not in git)
├── requirements.txt          # Dependencies
├── app.py                    # Main application
├── gunicorn.log              # Logs
├── uploads/                  # Temp files
├── templates/
│   └── index.html           # Web interface
└── static/
    └── styles.css           # Styling
```

---