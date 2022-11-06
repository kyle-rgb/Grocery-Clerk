FROM node:16.17.1-bullseye-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y wget gnupg \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list' \
    && apt-get update \
    && apt-get install -y google-chrome-stable fonts-ipafont-gothic fonts-wqy-zenhei fonts-thai-tlwg fonts-kacst fonts-freefont-ttf libxss1 \
      --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update \
    && apt-get install -y fluxbox gconf-service libasound2 libatk1.0-0 libc6 libcairo2 libcups2 libdbus-1-3 libexpat1 libfontconfig1 libgcc1 libgconf-2-4 \
    libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libpango-1.0-0 libpangocairo-1.0-0 libstdc++6 libx11-6 \
    libx11-xcb1 libxcb1 libxcomposite1 libxcursor1 libxdamage1 libxext6 libxfixes3 libxi6 libxrandr2 libxrender1 \
    libxss1 libxtst6 ca-certificates fonts-liberation libappindicator1 libnss3 lsb-release \
    xdg-utils wget wmctrl x11vnc x11-xkb-utils xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic x11-apps xvfb

ENV PUPPETEER_SKIP_CHROMIUM_DOWNLOAD true

COPY ./package.json /app/

RUN npm install \
    && groupadd -r pptruser && useradd -r -g pptruser -G audio,video pptruser \
    && mkdir -p /home/pptruser/Downloads \
    && chown -R pptruser:pptruser /home/pptruser \
    && chown -R pptruser:pptruser /app/node_modules \
    && chown -R pptruser:pptruser /app/package.json \
    && chown -R pptruser:pptruser /app/package-lock.json

COPY . /app/

RUN mkdir ./tmp && chown -R pptruser:pptruser ./tmp/

USER pptruser

RUN gpg --import /app/kyleA.gpg

CMD '/app/bootstrap.sh'