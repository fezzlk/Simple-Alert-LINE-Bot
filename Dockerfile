FROM python:3.11-slim

WORKDIR /app

# 週次習慣カレンダー画像(Pillow)で日本語テキストを描画するためのCJKフォント。
# fonts-noto-cjk は Debian の無料パッケージ(apt)。追加の金銭コストはなく、
# イメージビルド時間・サイズがわずかに増える程度。
RUN apt-get update \
    && apt-get install -y --no-install-recommends fonts-noto-cjk \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r /app/requirements.txt

COPY ./ /app

CMD ["sh", "-c", "gunicorn -b 0.0.0.0:${PORT} src:app"]
