# Stage 0 dev image. This deliberately runs `next dev`, not a production
# build — a production multi-stage image (build → standalone output →
# minimal runtime) is a later-stage concern once there's a real app to
# ship, not a Stage 0 scaffold decision.
FROM node:22-slim

WORKDIR /app

# Install dependencies first so Docker layer caching skips this step
# when only application code changes, not package.json/package-lock.json.
COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
