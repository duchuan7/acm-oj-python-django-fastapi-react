FROM eclipse-temurin:21-jdk-jammy
RUN apt-get update && apt-get install -y --no-install-recommends gcc g++ python3 time && rm -rf /var/lib/apt/lists/* \
    && useradd -u 10001 -m contestant && mkdir /work && chmod 777 /work
WORKDIR /work
USER 10001
CMD ["/bin/true"]

