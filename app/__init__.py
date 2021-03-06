import boto3
from boto3.dynamodb.conditions import Attr
import datetime

from flask import Flask, jsonify
from flask_s3 import FlaskS3
from flask import render_template, request, url_for

app = Flask(__name__, instance_relative_config=True)

# Load the default configuration
app.config.from_object('config')
app.config.from_pyfile('development.py')
app.config['UPLOAD_FOLDER'] = 'app/static/img/upload'
app.config['FLASKS3_BUCKET_NAME'] = 'zappa-static-files-yuanyi'

s3 = boto3.resource('s3',
                    aws_access_key_id=app.config['AWS_ACCESS_KEY_ID'],
                    aws_secret_access_key=app.config['AWS_SECRET_ACCESS_KEY'])

lambda_client = boto3.client('lambda')
dynamodb = boto3.resource('dynamodb')

flask_s3 = FlaskS3(app)
flask_s3.init_app(app)


# Route for the welcome page
@app.route('/')
@app.route('/welcome')
def welcome():
    return render_template('welcome.html')


# Route for the signin page
@app.route('/signin')
def signin():
    return render_template('signin.html')


# Route for the register page
@app.route('/register')
def register():
    return render_template('register.html')


# Route for the verify page
@app.route('/verify')
def verify():
    return render_template('verify.html')


@app.route('/verify_success')
def verify_success():
    email = request.args.get('email')
    print(email)
    # TODO: Create a new item for this user

    table = dynamodb.Table('user')
    table.put_item(
        Item={
            'username': email
        }
    )

    return render_template('signin.html')


@app.route('/run_code')
def run_code():
    username = request.args.get('username', 0, type=str)
    lang = request.args.get('lang', 0, type=str)
    questionName = request.args.get('codename', 0, type=str)
    code = request.args.get('code', 0, type=str)
    input = request.args.get('input', 0, type=str)

    print("username:" + username)
    print("language:" + lang)
    print("question name:" + questionName)
    print("input:" + str(input))
    print("code:" + code)

    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')

    if lang == "python":
        s3_url = lang + "/" + username + "/" + questionName + "/" + timestamp + "/" + questionName + ".py"
        s3.Object("test-yuanyi", s3_url).put(Body=code)

        response = lambda_client.invoke(
            FunctionName='run_python',
            InvocationType='RequestResponse',
            LogType='Tail',
            Payload='{"name":"' + questionName + '","input":' + '\"' + str(
                input) + '\"' + ',"url":"https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}'
            # Payload='{"url": "https://s3.amazonaws.com/test-yuanyi/javatest.java","name": "javatest"}'
        )
        print('{"name":"' + questionName + '","input":' + '\"' + str(
            input) + '\"' + ',"url":"https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}')

    elif lang == "java":
        s3_url = lang + "/" + username + "/" + questionName + "/" + timestamp + "/" + questionName + ".java"
        s3.Object("test-yuanyi", s3_url).put(Body=code)

        response = lambda_client.invoke(
            FunctionName='run_java',
            InvocationType='RequestResponse',
            LogType='Tail',
            # Payload='{"name":"fizzBuzz","input":[10],"url":"https://s3.amazonaws.com/test-yuanyi/'+path+'"}'
            Payload='{"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}'
        )
        print('{"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}')

    elif lang == "ruby":
        s3_url = lang + "/" + username + "/" + questionName + "/" + timestamp + "/" + questionName + ".rb"
        s3.Object("test-yuanyi", s3_url).put(Body=code)

        response = lambda_client.invoke(
            FunctionName='run_ruby',
            InvocationType='RequestResponse',
            LogType='Tail',
            # Payload='{ "input": "[1,2,3,4,5]","name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}'
            Payload='{ "input":'+ '\"'+ str(input) +'\"' + ',"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}'
        )
        # print('{"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}')
        print('{ "input":'+ '\"'+ str(input) +'\"' + ',"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}')

    elif lang == "javascript":
        s3_url = lang + "/" + username + "/" + questionName + "/" + timestamp + "/" + questionName + ".js"
        s3.Object("test-yuanyi", s3_url).put(Body=code)

        response = lambda_client.invoke(
            FunctionName='run_javascript',
            InvocationType='RequestResponse',
            LogType='Tail',
            # Payload='{"name":"fizzBuzz","input":[10],"url":"https://s3.amazonaws.com/test-yuanyi/'+path+'"}'
            # Payload='{ "input": "[1,2,3,4,5]","name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}'
            Payload='{ "input":'+ '\"'+ str(input) +'\"' + ',"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}'
        )
        print ('{ "input":' + '\"' + str(input) + '\"' + ',"name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}')

        # print(
            # '{"input": "[3,4]","name": "' + questionName + '","url": "https://s3.amazonaws.com/test-yuanyi/' + s3_url + '"}')
    else:
        return jsonify(result="Please select a correct programming language")

    result = response['Payload'].read().decode('ascii')

    # record info
    table = dynamodb.Table('user_question')
    table.put_item(
        Item={
            'username': username,
            'question_name': questionName,
            'code_s3_url': "https://s3.amazonaws.com/test-yuanyi/" + s3_url,
            'post_date_time': timestamp
        }
    )

    # submission# +1
    table = dynamodb.Table('question')
    response = table.get_item(
        Key={
            'question_name': questionName
        })
    count = response['Item']['total_submission']
    table.update_item(
        Key={
            'question_name': questionName,
        },
        UpdateExpression='SET total_submission = total_submission + :val',
        ExpressionAttributeValues={
            ':val': 1
        }
    )

    return jsonify(result=result)


# Route for the home page
@app.route('/home', methods=['GET', 'POST'])
def home():
    
    return render_template('home.html')


@app.route('/home/<username>', methods=['GET', 'POST'])
def userHome(username):
    username = username.replace(" ",".")
    table = dynamodb.Table('user_question')
    response = table.scan(
            FilterExpression=Attr('username').contains(username)
        )
    
    return render_template('home.html',list = response['Items'],username = username)

@app.route('/problems', methods=['GET', 'POST'])
def problems():
    table = dynamodb.Table('question')
    response = table.scan()

    if request.method=="POST":
        search_content = request.form['search']
        if search_content!="":
            response = table.scan(
                FilterExpression=Attr('question_name').contains(search_content)
            )
    

    return render_template('problems.html', list=response['Items'])

@app.route('/home/<username>/details/<question_name>')
def details(username,question_name):
    table = dynamodb.Table('question')
    response = table.get_item(
        Key={
            'question_name': question_name
        })
    description = response['Item']['question_content']

    table2 = dynamodb.Table('user_question')
    response = table2.get_item(
        Key={
        'username':username,
        'question_name':question_name
        })
    pre_code = response['Item']['code_s3_url'][37:]

    bucket = s3.Bucket('test-yuanyi')
    obj = bucket.Object(pre_code)
    body = obj.get()['Body'].read().decode('ascii')


    return render_template('details.html',description = description, body = body)

@app.route('/problems/<question_name>', methods=['GET', 'POST'])
def problem(question_name):
    description = ""
    table = dynamodb.Table('question')
    response = table.get_item(
        Key={
            'question_name': question_name
        })
    description = response['Item']['question_content']

    return render_template('problem.html', description=description, question_name=question_name)


if __name__ == '__main__':
    app.run()
