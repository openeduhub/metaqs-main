FROM apache/superset
# Switching to root to install the required packages
USER root
RUN pip install psycopg2-binary
RUN pip install elasticsearch-dbapi
# Switching back to using the `superset` user
USER superset