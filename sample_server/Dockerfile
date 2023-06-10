# Get the latest base image for python
FROM python:3
# Put files at the image '/server/' folder.
ADD server.py /server/
ADD flag /
# '/server/' is base directory
WORKDIR /server/
# Expose port 1337 in the container
EXPOSE 1337
# execute the command
CMD [ "python3", "/server/server.py", "1337" ]