# FROM node:lts-trixie
FROM oven/bun:latest

WORKDIR /app
COPY package.json bun.lock* ./
RUN rm -rf node_modules && bun install --force
COPY . .
EXPOSE 5173
CMD ["bun", "run", "dev", "--", "--host"]
