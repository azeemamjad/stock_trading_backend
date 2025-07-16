FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# ✅ Make sure wait-for-it is executable
RUN chmod +x wait-for-it.sh

# Default CMD if not overridden
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
