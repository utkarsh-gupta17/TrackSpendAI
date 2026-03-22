# Use a lightweight official Python 3.11 image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /code

# Install necessary system dependencies if any are needed for PDF parsing/pandas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt


# Copy the entire backend directory into the container
COPY . .

# Set up the internal HuggingFace routing port (Spaces requires 7860)
EXPOSE 7860

# Start the uvicorn server on the required port
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1"]
