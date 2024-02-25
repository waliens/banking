#!/bin/sh

VERSION=$1

if [ -z "$VERSION" ]; then
    echo "no version provided, skipping build"
    exit 1
else
    echo "building for version $VERSION"
fi

echo "building server..."
docker build -t rmormont/banking-server:latest -t rmormont/banking-server:$VERSION --target server server/
if [ $? -ne 0 ]; then
  echo "/!\ server build failed, aborting..."
fi

echo "building task runner..."
docker build -t rmormont/banking-task-runner:latest -t rmormont/banking-task-runner:$VERSION --target task-runner server/
if [ $? -ne 0 ]; then
  echo "/!\ task-runner build failed, aborting..."
fi

echo "building frontend..."
docker build -t rmormont/banking-ui:latest -t rmormont/banking-ui:$VERSION --target prod-server frontend/
if [ $? -ne 0 ]; then
  echo "/!\ ui build failed, aborting..."
fi

echo "building reverse-proxy..."
docker build -t rmormont/banking-reverse-proxy:latest -t rmormont/banking-reverse-proxy:$VERSION
if [ $? -ne 0 ]; then
  echo "/!\ reverse-proxy build failed, aborting..."
fi

# echo "pusing all images"
docker push rmormont/banking-server:latest
docker push rmormont/banking-server:$VERSION
docker push rmormont/banking-task-runner:latest
docker push rmormont/banking-task-runner:$VERSION 
docker push rmormont/banking-ui:latest
docker push rmormont/banking-ui:$VERSION 
docker push rmormont/banking-reverse-proxy:latest
docker push rmormont/banking-reverse-proxy:$VERSION 