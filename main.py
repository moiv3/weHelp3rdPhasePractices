from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import os
import uuid
import boto3
import mysql.connector
from aws_advanced_python_wrapper import AwsWrapperConnection
from mysql.connector import Connect
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from dotenv import load_dotenv
load_dotenv()

# db config
db_to_use = os.getenv("db_to_use")
if db_to_use == "aws_rds":
    db_host = os.getenv("db_host_aws_rds")
elif db_to_use == "local":
    db_host = os.getenv("db_host_local")
db_user = os.getenv("db_user")
db_pw = os.getenv("db_pw")
db_database=os.getenv("db_database")

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the S3 client
s3_client = boto3.client('s3', region_name=os.getenv("region_name"), 
                         aws_access_key_id=os.getenv("aws_access_key_id"),
                         aws_secret_access_key=os.getenv("aws_secret_access_key"))

BUCKET_NAME = os.getenv("s3_bucket_name")
CLOUDFRONT_URL = os.getenv("cloudfront_distribution_domain_name")

@app.get("/", include_in_schema=False)
async def index(request: Request):
    return FileResponse("./index.html", media_type="text/html")

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...), message: str = Form(...)):
    try:
        unique_id = str(uuid.uuid4())
        unique_filename = f"{unique_id}_{file.filename}"
        s3_client.upload_fileobj(file.file, BUCKET_NAME, unique_filename)
        # file_url = f"https://{BUCKET_NAME}.s3.amazonaws.com/{unique_filename}"
        file_url = f"https://{CLOUDFRONT_URL}/{unique_filename}"
        """
        create table message(
        id int auto_increment,
        message varchar(255) not null,
        image_url varchar(255) not null,
        create_time datetime not null default current_timestamp,
        primary key(id)
        );
        """        

        # save to database
        if db_to_use == "aws_rds":
            with AwsWrapperConnection.connect(
                Connect,
                f"host={db_host} database={db_database} user={db_user} password={db_pw}",
                plugins="failover",
                # wrapper_dialect="aurora-mysql",
                # autocommit=True) as awsconn:
                wrapper_dialect="aurora-mysql") as website_db:
                website_db_cursor = website_db.cursor()
        elif db_to_use == "local":
            website_db = mysql.connector.connect(host=db_host, user=db_user, password=db_pw, database=db_database)
            website_db_cursor = website_db.cursor()
        else:
            print("dotenv abnormal")
            return {"error": True, "message": "Check db connection"}
        
        cmd = "INSERT INTO message (message, image_url) VALUES (%s, %s)"
        website_db_cursor.execute(cmd, (message, file_url))
        website_db.commit()

        return {"ok": True, "filename": unique_filename}
    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(status_code=403, detail="Could not authenticate to S3")
    except Exception as e:
        print(str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/readMessages/")
async def read_messages():
    # read from database limit 5
    if db_to_use == "aws_rds":
        with AwsWrapperConnection.connect(
            Connect,
            f"host={db_host} database={db_database} user={db_user} password={db_pw}",
            plugins="failover",
            # wrapper_dialect="aurora-mysql",
            # autocommit=True) as awsconn:
            wrapper_dialect="aurora-mysql") as website_db:
            website_db_cursor = website_db.cursor()
    elif db_to_use == "local":
        website_db = mysql.connector.connect(host=db_host, user=db_user, password=db_pw, database=db_database)
        website_db_cursor = website_db.cursor()
    else:
        print("dotenv abnormal")
        return {"error": True, "message": "Check db connection"}
    
    cmd = "SELECT * FROM message ORDER BY create_time DESC LIMIT 5"
    website_db_cursor.execute(cmd)
    data = website_db_cursor.fetchall()
    print(data)
    output_list = []
    for item in data:
        item_dict = {}
        item_dict["id"] = item[0]
        item_dict["message"] = item[1]
        item_dict["image_url"] = item[2]
        item_dict["create_time"] = item[3]
        output_list.append(item_dict)
    return(output_list)


@app.get("/download/{filename}")
async def download_file(filename: str):
    try:
        s3_client.download_file(BUCKET_NAME, filename, filename)
        s3_object = s3_client.get_object(Bucket=BUCKET_NAME, Key=filename)
        file_stream = s3_object['Body']
        return StreamingResponse(file_stream, media_type="image/jpeg")
    except s3_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="File not found")
    except (NoCredentialsError, PartialCredentialsError):
        raise HTTPException(status_code=403, detail="Could not authenticate to S3")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from fastapi.responses import FileResponse, StreamingResponse

@app.get("/", include_in_schema=False)
async def index(request: Request):
    return FileResponse("./index.html", media_type="text/html")
