FROM node:14-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:14-alpine
COPY --from=builder /app/dist /app/

EXPOSE 80
CMD ["node", "/app/server.js"]
