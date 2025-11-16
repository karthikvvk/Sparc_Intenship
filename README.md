# Sparc Internship Project **This Branch only contains work by me.**

# Warning 
The Ai may be less accurete. Please Re-Verify the Output with actual Doctor.


# Prerequisites
- **Python 3.8 or higher**
- **MySQL Server**
- **CPU core >=2**
- **GPU >= 20GB**

# Models Used
- InternLM-S1-Mini
- Medgemma
- Qwen-5b-it


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

### 3. HF Login (Copy-Paste in CLI)
```
pip install huggingface_hub
python
from huggingface_hub import login
login(new_session=False)
exit()
```


### 4. Install Dependencies
```bash
pip install -r requirements.txtt
```
---
### 5. Setting Up Dependencies
#### **This Sets up the dependencies and enviroinment, creates Dirs and files needed. U can use this whenever u need to fresh up the DB/Server/DepndenciesFiles**
```bash
python Starter.py
```
---
### 6. Run Server
```bash
python Server.py
```

---
### 7. Run FrontEnd
```
cd frontend
npm run dev
```