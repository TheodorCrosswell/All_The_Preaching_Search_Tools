# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt
COPY /backend/requirements.txt /backend/requirements.txt

# Install any needed packages specified in requirements.txt
RUN apt-get update && apt-get install -y build-essential
RUN pip install --no-cache-dir --timeout=1000 torch --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r /backend/requirements.txt

# Copy the repository files
COPY . .

# Expose the port that Streamlit runs on
EXPOSE 8000

# Define the command to run your app
ENTRYPOINT ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]