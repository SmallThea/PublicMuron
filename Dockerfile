FROM python:3

RUN mkdir /app 
WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

CMD [ "python", "./muron/run.py" ]