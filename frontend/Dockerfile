FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_KEYCLOAK_URL=http://localhost:8080
ARG VITE_KEYCLOAK_REALM=taskapp
ARG VITE_KEYCLOAK_CLIENT_ID=task-frontend
ARG VITE_TASK_API_URL=http://localhost:8001
ARG VITE_REPLICA_API_URL=http://localhost:8002
RUN npm run build

FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html
