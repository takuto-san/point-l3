FROM swaggerapi/swagger-ui:v5.25.3

COPY openapi.yml /spec/openapi.yml
ENV SWAGGER_JSON=/spec/openapi.yml

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
