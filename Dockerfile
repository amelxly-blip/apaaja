FROM node:20-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends lua5.4 && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY package.json ./
COPY server.js ./
COPY public ./public
ENV NODE_ENV=production
EXPOSE 3000
CMD ["npm", "start"]
