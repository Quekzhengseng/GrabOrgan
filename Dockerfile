# Use a lightweight Python image
FROM python:3-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy dependencies file and install them
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy all microservice files
COPY . ./


# Expose the required ports
EXPOSE 5000 5001 5002 5003 5004 5100 5672 15672

# Define the entry point, will override in compose.yaml later
CMD ["python", "book.py"]