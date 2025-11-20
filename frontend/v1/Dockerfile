# Development Dockerfile for React frontend (hot reload)
FROM node:25-alpine AS build
WORKDIR /app

# Install dependencies
COPY package.json ./
COPY zscaler-ca-chain.crt /usr/local/share/ca-certificates/
ENV NODE_EXTRA_CA_CERTS  /usr/local/share/ca-certificates/zscaler-ca-chain.crt
RUN --mount=type=cache,target=/root/.cache/npm,sharing=locked \
    npm install --legacy-peer-deps --force

# Copy source code
COPY . .

RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/nginx.conf
# Remove default nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy React build output to nginx html directory
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Run nginx
CMD ["nginx", "-g", "daemon off;"]