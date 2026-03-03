## RAG Rice Courses Scheduler   

## Team Members 

**Group 2 - generation** (retrieval pipeline finds top k most relevant courses, format into structured context block + pass to Ollama, made sure there was no hallucination, displays course codes, groups results by theme, prioritizes readability)\
&nbsp;&nbsp;&nbsp;&nbsp;Wendy Jin \
&nbsp;&nbsp;&nbsp;&nbsp;Grace Yang \
&nbsp;&nbsp;&nbsp;&nbsp;Ryan Pascual


## Running the app

The frontend is a Vite/React app and the backend is a Django REST API.

1. **Backend** (in one terminal):
	```bash
	cd backend
	source ../venv/bin/activate    # or activate your virtualenv
	pip install -r ../requirements.txt
	python manage.py migrate       # if you haven't already
	python manage.py runserver     # starts at http://localhost:8000
	```

2. **Frontend** (in another terminal):
	```bash
	cd frontend
	npm install
	npm run dev                   # starts Vite at http://localhost:5173
	```

	Vite is configured to proxy `/api` requests to `http://localhost:8000` so your React components can simply fetch `/api/ask/` without CORS errors.



