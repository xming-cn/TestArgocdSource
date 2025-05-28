FROM public.ecr.aws/docker/library/python:3.13-alpine
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 80
ENTRYPOINT python3 app.py