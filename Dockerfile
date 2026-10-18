FROM swaggerapi/swagger-ui:v5.25.3

COPY l3-management.openapi.yaml /spec/openapi.yaml
ENV SWAGGER_JSON=/spec/openapi.yaml

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget -q -O /dev/null http://127.0.0.1:8080/ || exit 1
