# Start from a lightweight Python base image
FROM python:3-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy your requirements file into the container and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the composite microservice code into the container
COPY composite/requestOrgan/request_organ.py .


# Expose the port your service listens on (5021 by default)
EXPOSE 5021

# Set the default command to run your composite service
CMD ["python", "request_organ.py"]
