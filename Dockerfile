# 
FROM python:3.12

# 
WORKDIR /code

# 
COPY ./requirements.txt /code/requirements.txt

# 
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

#
COPY ./static /code/static

# 
COPY . /code

# 
CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]