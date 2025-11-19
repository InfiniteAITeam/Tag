#Prerequisites
   ->WSL install(recommended)
   ->Python 3.10+ inside WSL(python3 --version)
   ->take this repo as reference to tag https://github.com/SushilaGadal91/ResidentPortal

#Install & Open WSL
  ->Installing WSL
    wsl --install ubuntu
  ->Set up Linux user info
  ->Open WSL
    wsl

#Clone the project(inside WSL)
   cd ~
   git clone<REPO_URL>
   cd <YourProjectName>

#To run Project locally
 
#Create & activate a virtual environment
   python3 -m venv .venv             
   source .venv/bin/activate        

#Install dependencies
   pip install --upgrade pip
   pip install -r requirements.txt

#Configure environment
   Common variables:
   FastAPI server
   API_HOST=<127.0.0.1>
   API_PORT=<8000>

  OPENAI_API_KEY=<Your KEY>

 #Run the backend
  ->From the project root (with venv active):
    python api_server.py

#Typical workflow (curl examples)

Paths below assume WSL. If your files live on Windows

1 Generate TechSpec (if your generator uses AC & Figma)
	curl -X POST http://127.0.0.1:8000/generate-techspec
  	-H "Content-Type: application/json" \
  	-d '{
        "ac_local_file": "/mnt/c/Users/<you>/Documents/acceptance-criteria.md",
       	"figma_file_url": "https://www.figma.com/file/..."
     	}'

2 Suggest Tagging (points to your repo)
	curl -X POST http://127.0.0.1:8000/suggest-tagging
  	-h "Content-Type: application/json" \
  	-d '{"repo_path": "/mnt/c/Users/<you>/AppSelector/reactProject"}'

3 Apply Tagging (creates backups like *.taggingai.bak)
	curl -X POST http://127.0.0.1:8000/apply-tagging

4 View differences
	curl GET http://127.0.0.1:8000/view-difference

5 Roll back changes
	curl -X POST http://127.0.0.1:8000/rollback-changes
 	 -H "Content-Type: application/json" \
 	 -d '{"repo_path": "/mnt/c/Users/<you>/AppSelector/react-kiosk-billing-js"}