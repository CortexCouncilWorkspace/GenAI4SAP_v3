#Base Image to use
FROM python:3.12

EXPOSE 8084
WORKDIR /genai4sap
COPY . ./

#install all requirements in requirements.txt
RUN pip install -r requirements.txt

# Run the web service on container startup
CMD ["python3", "app.py"]
