FROM python:3.11-slim

WORKDIR /app

# COPY requirements.txt /app/
COPY requirements.txt .

# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install -r requirements.txt

# COPY . /app/
COPY . .

# COPY .env /app/  # Copy the .env file

EXPOSE 5000

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0"]
