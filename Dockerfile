FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    fonts-liberation \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

RUN sed -i 's/rights="none"/rights="read|write"/' /etc/ImageMagick-6/policy.xml && \
    sed -i 's/rights="none"/rights="read|write"/' /etc/ImageMagick-6/policy.xml

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p inputs/TrueMan inputs/Sport inputs/tech music_library ready_shorts

ENV FMPEG_BINARY="/usr/bin/ffmpeg"
ENV IMAGEMAGICK_BINARY="/usr/bin/identify"

CMD ["python", "main.py"]
