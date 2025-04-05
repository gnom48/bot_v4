FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /.

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./ ./

CMD ["sh", "-c", "python main.py"]