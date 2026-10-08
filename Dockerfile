# The image is created using Python 3.11
FROM python:3.11-slim

# Setting up the internal folder
WORKDIR /app

# Install OS-level dependencies/programs that pytesseract and pdf2image depend on
RUN apt-get update && apt-get install -y \
        tesseract-ocr \
        poppler-utils \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Make a copy of the requirements.txt file into the image
COPY requirements.txt .
# Install the requirements.txt on the image
RUN pip install --no-cache-dir -r requirements.txt

# Copy the code into the image
# . .: 
COPY . . 

# which port the image needs to use
EXPOSE 8502

# CMD: command to run the streamlit app, it is the same I am opening 
# the cmd on my local machine and type this command
CMD [ "streamlit", "run", "app.py", "--server.port=8502", "--server.address=0.0.0.0" ]



