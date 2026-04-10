# Base image
FROM python:3.11

# Set working directory
WORKDIR /app

# Copy dependencies first (for caching)
COPY requirements.txt ./

# Install dependencies
RUN pip3 install -r requirements.txt

# Copy all project files
ADD . .

# (No port needed? Because this is not a web server)

# Run the ML script
CMD ["python3", "main.py"]