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
EXPOSE 5672 15672 5001 5002 5003 5004 5005 5006 5007 5008 5009 5010 5011 5012 5013 5020 2021 2022 5023 5024 5025

# Define the entry point, will override in compose.yaml later
CMD ["python", "activity_log.py"]