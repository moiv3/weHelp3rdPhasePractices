# Stage3 Backend Project README

## AWS RDS
1. Run an AWS RDS instance (MySQL 8.0)

2. This RDS is configured to link to EC2, only that EC2 can link to RDS.

3. Use below command to signin to RDS:
```
>mysql -h {RDS host} -u {user} -p
```

4. In the Python code, we can still use mysql-connector-python to connect into RDS. Just replace "host=localhost" with "host={RDS host}" and provide the credentials.

5. In my case, I used an variable in .env (db_to_use = "aws_rds" or "local") & an if-else statement in Python code to switch between using localhost and AWS RDS, it works.

6. To run localhost db, might need to create a MySQL image. (Not used this time)

## AWS S3 & Cloudfront

After activating a S3 bucket, use Python boto3 library to upload files and respond the URL to the front end.

Uploaded files have a Object URL. First use this s3 URL to render images.

```
https://{bucket}.s3.us-west-2.amazonaws.com/{image}.jpg 
```

Then set up Cloudfront to link to that S3 bucket.

Cloudfront generates a domain name for this link(distribution).

Then we can replace Object URL with:
```
https://{some_string}.cloudfront.net/{image}.jpg
```
Now, when we render this image, Cloudfront optimizes the distribution for us.

## Docker Deployment

### Docker desktop

Docker desktop was installed and logged in.

Followed Getting started guide to build an example project.

** Note: Remove those images?

To build this project in docker:

1. Generate/Write requirements.txt

Go to EC2 instance, cd to project folder, activate virtual env, then run command:

```pip freeze > requirements.txt```

2. Write Dockerfile

From FastAPI documentation, take the example Dockerfile and modify as below:

```
# Select Required Python Version
FROM python:3.12

# Declare working directory
WORKDIR /code

# First copy requirements.txt so we can install
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy static files (not sure if really needed, test)
COPY ./static /code/static

# Copy code
COPY . /code

# Run app
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

3. Add .dockerignore

Adding .dockerignore can avoid packaging in information when building an image.
The image building engine ignores files matching the pattern in .dockerignore.

I use the following contents for my .dockerignore:

```
Dockerfile
.dockerignore
.env
```

Refernce website: https://shisho.dev/blog/posts/how-to-use-dockerignore/

4. Build the image

https://docs.docker.com/reference/cli/docker/buildx/build/

-t = --tag, followed by desired tag
. means current directory

```
docker build -t moiv3/wehelp3rdphaseimage .
```

5. Upload to dockerhub

Create a repo on docker hub, then

```
docker push moiv3/wehelp3rdphaseimage:latest

> ...
latest: digest: sha256:e0624268de38645c3c17e30412fbf5f47b7ac3a06f2f455b0a79dda572ff0e93 size: 3049
```

6. Go to EC2, pull the image

Sign in to docker
```
docker login registry-1.docker.io -u {username}
Password: {personal access token}
```

Pull image, then check
```
sudo docker pull moiv3/wehelp3rdphaseimage:latest
sudo docker images
```

Run image
```
sudo docker run -d --name mycontainer -p 8000:8000 --env-file '.env' moiv3/wehelp3rdphaseimage:latest
```

Check running status
```
sudo docker ps
sudo docker logs {container} --follow
```

Stop/Start container
```
docker stop {container}
docker start {container}
```

## Domain Name

1. Buy a domain name from GoDaddy.

2. In GoDaddy console, Select {Your Domain} -> DNS

3. “A” record, Name=@, Points to=EC2 elastic IP

4. Save and wait for change.

Reference: https://manushka.medium.com/how-to-point-your-godaddy-domain-to-aws-ec2-instance-29011697ec1b

Reference: https://articles.onlinetoknow.com/dns/