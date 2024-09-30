import os
os.environ['MPLCONFIGDIR'] = '/tmp'
import json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import io
import boto3
import ast


s3_bucket = os.environ['S3_BUCKET']

def bar_chart(title, x_values, y_values, x_label, y_label):
    
    x_values_parsed= ast.literal_eval(x_values)
    y_values_parsed= ast.literal_eval(y_values)
  
    fig, ax = plt.subplots(figsize=(10, 6))  
    ax.bar(x_values_parsed, y_values_parsed, color='blue')
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    
  
    output_name=f"{title}.png"
    
    img_data = io.BytesIO()
    fig.savefig(img_data, format='png')
    img_data.seek(0)
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(s3_bucket)
    KEY = 'graphs/' + str(output_name)
    bucket.put_object(Body=img_data, ContentType='image/png', Key=KEY)
    
    
    result = f'Your bar chart named {title} is saved to your s3 bucket'
    print(result)

    return 


def handler(event, context):
    # TODO implement
    
    agent = event['agent']
    actionGroup = event['actionGroup']
    function = event['function']
    parameters = event.get('parameters', [])
    try:
        if function == "bar_chart":
            for param in parameters:
                if param["name"] == "title":
                    title = param["value"]
                if param["name"] == "x_values":
                    x_values = param["value"]
                if param["name"] == "y_values":
                    y_values = param["value"]
                if param["name"] == "x_label":
                    x_label = param["value"]
                if param["name"] == "y_label":
                    y_label = param["value"]
                
 
        # Execute your business logic here. For more information, refer to: https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html
        bar_chart(title,x_values, y_values, x_label, y_label)
        print('successfully finished')
        responseBody = {
            "TEXT": {
                "body": "The function {} was called successfully!".format(function)
            }
        }
    except Exception as e:
        responseBody = {
            "TEXT": {
                "body": "An error occurred: {}".format(str(e))
            }
        }
    
    action_response = {
        'actionGroup': actionGroup,
        'function': function,
        'functionResponse': {
            'responseBody': responseBody
        }

    }

    dummy_function_response = {'response': action_response, 'messageVersion': event['messageVersion']}
    print("Response: {}".format(dummy_function_response))

    return dummy_function_response
