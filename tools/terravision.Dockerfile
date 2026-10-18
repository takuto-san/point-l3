FROM patrickchugh/terravision@sha256:6bb96c63cc6f072014c58a665e5c4cc53dd0f29976b4f6e774edf5536915e786
USER root
# Japanese account and service labels must be readable in the exported PNG.
RUN apk add --no-cache font-noto-cjk
# Expose built-in ML service icons with TVG helper names (not Terraform resources).
COPY terravision-services.pth /usr/lib/python3.12/site-packages/terravision-services.pth
USER terravision
