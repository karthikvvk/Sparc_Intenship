# Sparc_Intenship
This repo only contains work by me. For Full version Refer the Sparc's Orginal Repo at LINK

# Sparc Internship Project

A Python and MySQL-based summarization server.

---

## Table of Contents
1. [Prerequisites](#prerequisites)  
2. [Installation](#installation)  
   - [Clone Repository](#1-clone-repository)  
   - [Create Virtual Environment](#2-create-virtual-environment)  
   - [Install Dependencies](#3-install-dependencies)  
3. [Running the Server](#running-the-server)  
4. [Usage](#usage)  

---

## Prerequisites
- Python 3.8 or higher  
- pip (Python package installer)  
- MySQL Server  

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/karthikvvk/Sparc_Intenship.git
cd Sparc_Intenship
```

### 2. Create Virtual Environment

#### On Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
```

#### On Windows (PowerShell)
```powershell
python -m venv venv
.env\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

---

## Running the Server
```bash
python Server.py
```

---

## Usage
Once the server is running, open your browser and visit:

```
http://127.0.0.1:5000/start_summarisation
```

This will start the summarization process.
