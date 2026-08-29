FROM python:3.11-slim

WORKDIR /srv/hl7

RUN pip install --no-cache-dir httpx

COPY hl7_parser.py mllp_bridge.py ./

EXPOSE 6661
ENTRYPOINT ["python", "mllp_bridge.py"]
CMD ["--host", "0.0.0.0", "--port", "6661"]
