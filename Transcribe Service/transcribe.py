from flask import Flask, jsonify, request
from flask_restful import Resource, Api, reqparse
import requests
import boto3
import boto3.s3
import time
import urllib.request, json
import ssl
import botocore

app = Flask(__name__)

S3_BUCKET_NAME = "krithik-test"
FILE_PATH = "/Users/krithiktamilvanan/Downloads/"
AWS_REGION_NAME = "us-west-2"

@app.route('/transcripts', methods=['POST'])
def audio_to_text():
    """
    Checks transcription jobs to see if job with the file name already exists. If it exists, it will return the existing transcript for the file.
    If there is no job wiht the file name, it will upload the file to the s3 bucket and create a new transcription job.
    While the job is running, it will check for the status and result every 10 seconds for about 17 minutes (100 * 10 seconds).
    :return: transcribed text
    """
    #print("entering upload")
    #print("Posted file: {}".format(request.files['file']))
    input_file = request.files['file']
    input_file_content = get_file_contents(input_file)
    file_name = input_file.filename
    #print("This is your file name: " + file_name)
    try:
        transcript_text = get_transcription_job(file_name)
    except Exception as e:
        #print("Generating new transcript")
        s3_upload(file_name, input_file)
        #print("Uploaded file to S3")
        transcript_text = transcribe_audio(file_name, file_name)

    response = jsonify({"transcript": transcript_text})
    response.headers.add('Access-Control-Allow-Origin', '*')
    #print("Transcribed text: " + transcript_text)
    return response


def s3_upload(file_name, input_file):
    """
    Connects with s3 and creates a file under the given bucket name.
    :param file_name: name of the file the user uploaded, and is the name of the file in the s3 bucket.
    :param input_file: the file content
    :return: none
    """
    #print("Starting s3_upload")
    #print("This is your file name: " + file_name)
    try:
        s3_client = boto3.client('s3')
        response = s3_client.upload_file(FILE_PATH + file_name, S3_BUCKET_NAME, file_name, ExtraArgs={"ContentType": input_file.content_type})
        #print("Completed s3_upload")
    except botocore.exceptions.ClientError as error:
        #print("s3_upload error: " + str(error))
        raise error


def transcribe_audio(project_name, file_name):
    """
    This will start a transcription job in AWS to transcribe the user's given audio file.
    :param project_name: name under which the transcription job runs
    :param file_name: name of the file in the given s3 bucket
    :return: the transcribed text
    """
    #print("transcribe_audio project name: " + project_name)
    transcribe_client = get_transcribe_client()
    file_url = "s3://" + S3_BUCKET_NAME + "/" + file_name
    #print("File Url:" + file_url)
    transcribe_client.start_transcription_job(
        TranscriptionJobName = project_name,
        Media = {"MediaFileUri" : file_url},
        MediaFormat = 'mp3',
        LanguageCode = 'en-US'
    )

    count = 100
    
    while count > 0:
        transcript_text = get_transcription_job(project_name)
        if transcript_text is not None:
            #print(transcript_text)
            return transcript_text
        print("Transcribe in Progress")
        count -= 1
        time.sleep(10)
    #print("Took too long to transcribe")
    return "Took too long to transcribe"

def get_transcription_job(project_name):
    """
    This gets the transcription job back from AWS, and reads the status the job returned.
    If it is completed, a url will be present in the returned data.
    This url points to the transcribed text, which is stored in a common s3 bucket, and it will contain the transcribed text.
    By reading the url content, you can get the transcribed text from a dictionary.
    If it fails, it will return request failed.
    :param project_name:
    :return:
    """
    try:
        transcribe_client = get_transcribe_client()
        #print("This is your project name: " + project_name)
        project = transcribe_client.get_transcription_job(TranscriptionJobName = project_name)
        project_status = project["TranscriptionJob"]["TranscriptionJobStatus"]
        #print(f"Waiting for {project_name}. Current status is {project_status}.")
        if project_status in ["COMPLETED", "FAILED"]:
            #print(f"Project {project_name} is {project_status}.")
            if project_status == 'COMPLETED':
                #print(
                    #f"Download the transcript from\n"
                    #f"\t{project['TranscriptionJob']['Transcript']['TranscriptFileUri']}."
                    #f"\t{project}."
                #)
                ssl._create_default_https_context = ssl._create_unverified_context
                url = project['TranscriptionJob']['Transcript']['TranscriptFileUri']
                #print(url)
                response = urllib.request.urlopen(url)
                data = json.loads(response.read())
                text = data['results']['transcripts'][0]['transcript']
                print("This is your transcribed text: " + str(text))
                return str(text)
            else:
                return "Request Failed"
        else:
            return None
    except Exception as error:
        #print("get_transcription_job error: " + str(error))
        raise error


def get_transcribe_client():
    """
    Creates a transcribe client under the given region name.
    :return: Returns the transcribe client.
    """
    transcribe_client = boto3.client("transcribe", AWS_REGION_NAME)
    return transcribe_client

def get_file_contents(input_file):
    """
    Debug function for printing the bytes in the user's file.
    :param input_file: User uploaded file.
    :return: Returns bytes in the user's file.
    """
    #print("File name: " + input_file.filename)
    byte = input_file.read(1024)
    bytes = byte
    while byte:
        #print(byte)
        byte = input_file.read(1024)
        bytes += byte
    return bytes

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)