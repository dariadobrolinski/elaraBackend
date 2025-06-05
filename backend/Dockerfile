FROM python:3.10-slim


WORKDIR /backend

COPY requirements.txt .
RUN apt-get update && \
    apt-get install -y libglib2.0-0 libpango-1.0-0 libpangoft2-1.0-0 libpangocairo-1.0-0 libharfbuzz0b libfontconfig1 && \
    rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# Set the port the application will run on
ENV PORT 8000

# Expose the port
EXPOSE $PORT

# Command to run the application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]