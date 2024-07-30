# Stage3 Backend Project README

## Message Board System

In this repo is a simple message board system using HTML/CSS/JavaScript, FastAPI framework and MySQL DB.

At first the message board was connected to localhost MySQL DB, then moved to AWS RDS MySQL DB after RDS setup complete.

Pictures were first uploaded to AWS S3, then changed to Cloudfront Object URL after Cloudfront distribution setup complete.

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

To build this project in docker:

1. Generate/Write requirements.txt

Go to EC2 instance, cd to project folder, activate virtual env, then run command:

```pip freeze > requirements.txt```

2. Write Dockerfile

From FastAPI documentation: https://fastapi.tiangolo.com/deployment/docker/ Take the example Dockerfile and modify as below:

```
# Select Required Python Version
FROM python:3.12

# Declare working directory
WORKDIR /code

# First copy requirements.txt so we can install
COPY ./requirements.txt /code/requirements.txt

# Install dependencies
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Copy static files
COPY ./static /code/static

# Copy code
COPY . /code

# Run app
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

3. Add .dockerignore

Adding .dockerignore can avoid packaging in sensitive information (like keys, .envs...) when building an image.
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

-t = --tag, followed by desired tag, "." means build from current directory.

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

To map Elastic IP port 80 to container port 8000, use this instead:
sudo docker run -d --name mycontainer -p 80:8000 --env-file '.env' moiv3/wehelp3rdphaseimage:latest
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

5. Test docker on another EC2 instance

I started another EC2 instance. Only installed docker, did not install anything else.

docker pulled the image, then run in container. 

The website could run as expected, also connecting to the same db.

## Domain Name

1. Buy a domain name from GoDaddy.

2. In GoDaddy console, Select {Your Domain} -> DNS

3. “A” record, Name=@, Points to=EC2 elastic IP

4. Save and wait for change.

Reference: https://manushka.medium.com/how-to-point-your-godaddy-domain-to-aws-ec2-instance-29011697ec1b

Reference: https://articles.onlinetoknow.com/dns/

## HTTPS

nginx, certbot were used to achieve HTTPS.

### nginx

1. install nginx outside of docker.

2. I run the docker container at 8003 port, so edit nginx config file at /etc/nginx/sites-available/default to reverse proxy from 80 port to http://127.0.0.1:8003

```
location / {
                proxy_pass http://127.0.0.1:8003;
        }
```

test URL at port 80, it should work.

### certbot

Follow instructions https://certbot.eff.org/instructions?ws=nginx&os=ubuntufocal to install certbot.

If we use certbot --nginx to verify,
Certbot will create key files on the machine. 

Then, certbot will tell the remote server to visit our machine on port 80 to get these keys to verify.
So we have to open port 80 on our machine.

After checking port 80, run

```
sudo certbot --nginx
```

certbot will also ask if edit nginx config to redirect port 80 to port 443. I choose yes.

Test again using traces.fun:443, now HTTPS certificate is valid.

Test using traces.fun:80, redirects (HTTP code 301) to traces.fun:443

## Load Balancer(ELB)

A load balancer is a server that can redirect requests to a group of instances.

I Use Loader.io to test load.

### Max load for 1 instance: 400~500 requests/s

For 1 instance without load balancer, for 15 sec duration, The server can handle 400 requests/s but not 500 requests/s.

Then add load balancer.
First add with only 1 instance

Settings:
LB listens to port 443, routes to target group wehelp-tg4
wehelp-tg4 has 1 instance port 443.

Check connection ok.

Then redirect domain name DNS A record:

Was: Elastic IP
To be: Load balancer IPv4 DNS address.

So now, connections to the domain name will go to the ELB, then the ELB will direct to one of its targets. (As of now we have only one target.)

Then add more instances from AMI, then register them to target group.

Now, ELB will redirect requests to one of the two target instances.

### Max load for 2 instances + ELB: 900~1000 requests/s

For 2 instances with load balancer, for 15 sec duration, The server can handle 900 requests/s but not 1000 requests/s.

### Max load for 3 instances + ELB: 1300~1400 requests/s

For 3 instances with load balancer, for 15 sec duration, The server can handle 1300 requests/s but not 1400 requests/s.

### Max load for 3 instances + ELB, 1 down:

I shut down 1 instance and test again with 900 req/s.

Initially, we can see 33% error rate. Then, the error rate decreases to 0%.

ELB also detects this and routes the requests to the remaining 2 instances instead.

Run the test again, and the error rate is 0%.

### Conclusion: ELB can distribute load and detect failed instances.