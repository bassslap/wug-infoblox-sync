FROM python:3.12-slim

WORKDIR /app

# Install dependencies
RUN pip install --no-cache-dir Flask pyOpenSSL

# Copy application
COPY app.py .

# Expose HTTPS port
EXPOSE 443

# Run the mock Infoblox WAPI server
CMD ["python", "app.py"]
