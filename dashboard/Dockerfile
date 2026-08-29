FROM node:20-slim AS build
WORKDIR /srv/dashboard
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:alpine
COPY --from=build /srv/dashboard/dist /usr/share/nginx/html
EXPOSE 80
