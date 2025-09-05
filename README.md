# Sparc Internship Project This Branch only contains work by me.
This is a Python and MySQL-based summarization Ai mainly developed for Medical Use.
Uses MedGemmaQ4KM local model fro summarisation.

# Warning
 The Ai may be less accurete. Please Re-Verify the Output with actual Doctor.


# Prerequisites
- Python 3.8 or higher  
- pip (Python package installer)  
- MySQL Server  


# Installation
### 1. Clone Repository
#### Specific to this branch
```bash
git clone --branch summary https://github.com/ArokiaMartinN/Sparrc_Intern.git
cd Sparc_Intenship
(or)
#git clone https://github.com/ArokiaMartinN/Sparrc_Intern.git
#cd Sparc_Intenship
#git checkout summary
```
#### In General
```bash
git clone https://github.com/ArokiaMartinN/Sparrc_Intern.git
cd Sparc_Intenship
git checkout <BranchName_u_want>
```
---
### 2. Create Virtual Environment
#### On Linux / macOS
```bash
python3 -m venv venv
source venv/bin/activate
```
#### On Windows (PowerShell)
```powershell
python -m venv venv
.venv\Scripts\activate
```
---
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
---
### 4. Setting Up Dependencies
#### This Sets up the dependencies and enviroinment, creates Dirs and files needed. U can use this whenever u need to fresh up the DB/Server/DepndenciesFiles
```bash
python Starter.py
```
---
### 5. Running Server
```bash
python Server.py
```
