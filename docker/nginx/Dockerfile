FROM nginx:1.19-alpine

ENV TZ=Asia/Tokyo

RUN apk add --no-cache tini git tzdata \
    && cp /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
