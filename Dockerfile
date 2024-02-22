# Use the official Airflow image as the base
FROM apache/airflow:latest

# Switch to airflow User
USER airflow

# Install the Docker, HTTP, and Airbyte providers for Airflow
RUN pip install apache-airflow-providers-http \
  && pip install apache-airflow-providers-airbyte \
  && pip install apache-airflow-providers-mongo 
# pip install apache-airflow-providers-docker \
# Switch back to root user
USER root