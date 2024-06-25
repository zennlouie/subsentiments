# Use a base image with Python pre-installed
FROM python:3.12-slim

ENV PYTHONUNBUFFERED True

# Set the working directory inside the container
ENV APP_HOME /app
WORKDIR $APP_HOME
COPY . ./

# Copy the requirements.txt file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port that the app will run on
EXPOSE 5006

# Set the command to run the app when the container starts
CMD panel serve app.py --address 0.0.0.0 --port 8080 --allow-websocket-origin="*"