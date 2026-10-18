# syntax=docker/dockerfile:1

FROM swaggerapi/swagger-ui:v5.33.1

LABEL org.opencontainers.image.title="point-l3-openapi" \
      org.opencontainers.image.description="Swagger UI for the point L3 OpenAPI contract" \
      org.opencontainers.image.source="https://github.com/takuto-san/point-l3"

COPY --chmod=0444 openapi.yml /spec/openapi.yml
RUN chmod 0555 /spec

ENV SWAGGER_JSON=/spec/openapi.yml

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD wget --quiet --output-document=/dev/null http://127.0.0.1:8080/ || exit 1
