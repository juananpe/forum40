FROM node:lts-alpine as builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
ENV NODE_ENV=production
RUN npm run build

FROM nginx:stable-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
ENV NGINX_PORT=8080
EXPOSE 8080
