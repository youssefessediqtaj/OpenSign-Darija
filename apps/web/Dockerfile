FROM node:22-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:22-alpine AS build
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ARG VITE_API_BASE_URL=
ARG VITE_MEDIAPIPE_MODEL_PATH
ARG VITE_MEDIAPIPE_WASM_PATH
ARG VITE_CAMERA_DEFAULT_WIDTH
ARG VITE_CAMERA_DEFAULT_HEIGHT
ARG VITE_CAMERA_DEFAULT_FPS
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_MEDIAPIPE_MODEL_PATH=$VITE_MEDIAPIPE_MODEL_PATH
ENV VITE_MEDIAPIPE_WASM_PATH=$VITE_MEDIAPIPE_WASM_PATH
ENV VITE_CAMERA_DEFAULT_WIDTH=$VITE_CAMERA_DEFAULT_WIDTH
ENV VITE_CAMERA_DEFAULT_HEIGHT=$VITE_CAMERA_DEFAULT_HEIGHT
ENV VITE_CAMERA_DEFAULT_FPS=$VITE_CAMERA_DEFAULT_FPS
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY --from=build /app/node_modules/@mediapipe/tasks-vision/wasm /usr/share/nginx/html/mediapipe/wasm
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
