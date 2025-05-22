FROM python:3.12-slim
WORKDIR /SFSS
COPY . .
RUN pip install -r requirements.txt
RUN apt update && apt install -y libmagic-dev
RUN pip install waitress
RUN mkdir uploads
EXPOSE 5000
CMD ["waitress-serve", "--port=5000", "--call", "app:create_app"]