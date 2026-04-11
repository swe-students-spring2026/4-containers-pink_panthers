# Base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy dependencies first
COPY requirements.txt ./

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy all files
ADD . .

# Set environment variable for Flask
ENV FLASK_APP=app.py

# Expose Flask port
EXPOSE 5000

# Run Flask app
CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]