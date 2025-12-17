This is a simple FastAPI project designed to be run locally using a Python virtual environment. The API includes automatically generated documentation accessible at /docs using Swagger UI.

To get started, first create and activate a virtual environment:


python -m venv venv

Then activate it:

venv\Scripts\activate

After activation, install the required dependencies:

pip install -r requirements.txt

run with

uvicorn main:app --host 127.0.0.1 --port 8000

Here you can test the endpoints and explore the API

http://127.0.0.1:8000/docs




