FROM python:2.7

# Set the file maintainer (your name - the file's author)
MAINTAINER Lauri Junkkari

# Set env variables used in this Dockerfile
ENV PROJECT_NAME=palvelutori
ENV PROJECT_SRC=.
ENV PROJECT_SRVHOME=/srv
ENV PROJECT_SRVPROJ=/srv/${PROJECT_NAME}

# Create application subdirectories
WORKDIR $PROJECT_SRVHOME
RUN mkdir media static logs
VOLUME ["${PROJECT_SRVHOME}/media/", "${PROJECT_SRVHOME}/static/", "${PROJECT_SRVHOME}/logs/"]

ENV PROJECT_STATIC_ROOT=${PROJECT_SRVHOME}/static
ENV PROJECT_MEDIA_ROOT=${PROJECT_SRVHOME}/media

# Copy application source code
COPY $PROJECT_SRC $PROJECT_SRVPROJ

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r ${PROJECT_SRVPROJ}/requirements.txt -U

# Port to expose
EXPOSE 8000

# Copy entrypoint script into the image
WORKDIR ${PROJECT_SRVPROJ}
COPY ${PROJECT_SRC}/scripts/docker-entrypoint.sh /

ENTRYPOINT ["/docker-entrypoint.sh"]
