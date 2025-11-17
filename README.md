
# Guidance for Fraud Detection with Intelligent Document Processing on AWS

## Table of Contents

1. [Overview](#overview)
    - [AWS Services](#aws-services)
    - [Cost](#cost)
2. [Prerequisites](#prerequisites)
    - [Operating System](#operating-system)
3. [Deployment Steps](#deployment-steps)
4. [Deployment Validation](#deployment-validation)
5. [Running the Guidance](#running-the-guidance)
6. [Next Steps](#next-steps)
7. [Cleanup](#cleanup)

## Overview
Financial institutions face multifaceted challenges in modern claims processing, primarily stemming from the overwhelming 
influx of unstructured data (documents, images, videos, and audio recordings) that lacks predefined schema and standardized 
processing frameworks. <br/>
This solution focuses on automating multi-modal documents processing in insurance clasims. It extracts data from document forms, images and audio files and flow them through machine learning models and GenAI to derive insights to produce reports in both of human and machine readable formats.

![Architecture](doc/architecture.png)

### AWS Services
This solution consists of following key components:
* Amazon Bedrock Data Automation (BDA): A GenAI-powered capability of Bedrock that streamlines the extraction of valuable insights from unstructured, multimodal content like documents, images, audio, and videos. It is used for extract text from forms, extracting describtion of images and transcringing/summarizing audio clips from customer calls.
* Amazon SageMaker AI: A cloud-based machine learning(ML) platform that helps users build, train, and deploy ML models. The solution trains and deploys a document tampering detection model to SageMaker Endpoint for fraud-detection.
* Amazon S3, AWS Lambda, AWS Step Functions and Amazon DynamoDB: These AWS serverless services combines AI/ML functionalies into a seamless workflows.<br/>
<br/>

<details>
  <summary>Note on dataset and Acceptable End User Policy from the model provider</summary>

The dataset utilized in this guidance consists entirely of synthetic data. This artificial data is designed to mimic real-world information but does not contain any actual personal or sensitive information.

For use cases related to finance and medical insurance as used in this guidance:

Users must adhere to the model provider's Acceptable Use Policy at all times. This policy governs the appropriate use of the synthetic data and associated models, and compliance is mandatory.This synthetic data is provided for testing, development, and demonstration purposes only. It should not be used as a substitute for real data in making financial or medical decisions affecting individuals or organizations.
By using this dataset and guidance, you acknowledge that you have read, understood, and agree to comply with all applicable terms, conditions, and policies set forth by the model provider.

</details>

### Cost
The following table provides a sample cost breakdown for deploying this
Guidance with the default parameters in the US East (N. Virginia) Region
for one month.

| **AWS service**   | Dimensions                                             | Monthly cost \[USD\] |
| ----------------- | ------------------------------------------------------ | ---------------------------------------------- |
| Amazon S3 Standard	| S3 Standard storage (50 GB per month)	| $1.15 |
| Amazon S3 Data Transfer	| DT Inbound: Not selected (0 TB per month), DT Outbound: Not selected (0 TB per month)	| $0 |
| Step Functions - Standard Workflows	| Workflow requests (100 per day), State transitions per workflow (10)	| $0.66 |
| DynamoDB on-demand capacity | Table class (Standard), Average item size (all attributes) (1 KB), Data storage size (50 GB)	| $12.5 |
| SageMaker Serverless Inference | Requests units (millions), Requests units (millions), Number of request per month (1), Duration of each request (ms) (3000)	| $360.00 |
| Amazon Bedrock Nova Pro FM | Number of Input tokens (20 million per month), Number of output tokens (40 million per month)	| $144 |
| Bedrock Data Automation for blueprints	| 5 documents per claim  1 image per claim documents 100 claims per day, using custom blueprints monthly cost	 | $1200 |
| Total | | $1718.31 |

## Prerequisites
<br/>
- Python 3.10+<br/>
- [AWS CDK CLI](https://docs.aws.amazon.com/cdk/v2/guide/getting_started.html)<br/>
- [SageMaker AI execution IAM role](https://docs.aws.amazon.com/sagemaker/latest/dg/sagemaker-roles.html)<br/>
<br/>

### Operating System

#### Python virtual environment
To manually create a virtualenv on MacOS and Linux:

```bash
$ python3 -m venv .venv
```
## Deployment Steps

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```bash
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```bash
$ pip install -r requirements.txt
```

### SageMaker AI Endpoint
Open ```sagemaker/document-tampering-detection/config.ini``` and change the region parameter to desired value.

```ini
[AWS]
region = us-east-1
```

<br/>
Open a terminal and change the working directory to sagemaker/document-tampering-detection folder. Run a script as below.

```bash
$ cd sagemaker/document-tampering-detection
$ python train_and_deploy.py
```

The script will deploy a ML model to SageMaker AI endpoint with a name ```document-tampering-detection-v-DEMO```.

### Create Amazon Bedrock Data Automation(BDA) project and blueprints
Open a terminal and change to directory ```bedrock_data_automation``` and run a script. 

```bash
$ cd bedrock_data_automation
$ python bda_create_project.py
```

The script will produce a BDA project ARN at the end of execution.

#### Edit config.ini
Open ```config.ini``` file in the root of the project folder. Edit the values as required.

```ini
[BDA]
projectArn = <Project ARN created from the above step>

[AWS]
region = <AWS region>

[SM_ENDPOINT]
tampered_image_detection_endpoint = "document-tampering-detection-v-DEMO"

[NOTIFICATION]
complete_notification_reciepients = <Comma seperated list of emails to recieve task completion notifications>
```


### Deploy Backend Stacks
From the root of the project folder, run following command to deploy a documents processing workflow.

Remember to bootstrap before deploying stacks.
```bash
$ cdk bootstrap
```

```bash
$ cdk deploy InsuranceClaimProcessStack/InsuranceClaimProcessWorkflow
```

Then, deploy an API stack for the UI.

```bash
$ cdk deploy InsuranceClaimProcessApiStack/InsuranceClaimProcessApi
```

The above command will print out an URL for API endpoint at the end. For example:

```
Outputs:
InsuranceClaimProcessStackInsuranceClaimProcessApiFBBB0A99.InsuranceClaimApiEndpointA00BCDE11 = https://abcdef.execute-api.us-east-1.amazonaws.com/dev/
InsuranceClaimProcessStackInsuranceClaimProcessApiFBBB0A99.UserPoolClientId = xxxxxxxxxxxxxxxxxx
InsuranceClaimProcessStackInsuranceClaimProcessApiFBBB0A99.UserPoolId = us-east-1_xxxxxxxx
```

Copy the URL printed from the out for the next step.

### Deploy Front-end
Open a file ```frontend/src/common/constants.js``` and paste the URL copied from the above step to API_ENDPOINT,COGNITO_USER_POOL_ID and COGNITO_USER_POOL_CLIENT_ID constant:

```java
export const API_ENDPOINT = "https://abcdef.execute-api.us-east-1.amazonaws.com/dev/";
export const COGNITO_USER_POOL_ID = "us-east-1_xxxxxxxx";
export const COGNITO_USER_POOL_CLIENT_ID = "xxxxxxxxxxxxxxxxxx";
```

Change to ```frontend``` folder and run a command to build a single page application.

```bash
$ cd frontend
$ npm install
$ npm run build
```

After completion, change to the root of the project and deploy frontend UI stack using a CDK command.

```bash
$ cdk deploy InsuranceClaimProcessFrontEndStack/InsuranceClaimProcessFrontEnd
```

## Deployment Validation

At the end of the execution, following Output will be printed:

```
Outputs:
InsuranceClaimProcessStackInsuranceClaimProcessFrontEndDE27C08B.UIDomain = xxxxxxx.cloudfront.net
```

Open the URL in UIDomain output from a browser, which will show a login page.

## Running the Guidance

1. The claims analyst uploads sample documents via the Web Client to the Amazon Simple Storage Service (Amazon S3) bucket for blueprint creation. 

2. Amazon Bedrock Data Automation (Amazon BDA) uses JSON templates and Python scripts to create standardized blueprints for processing future claims file submissions.

3. Amazon BDA refines and stores custom blueprints.

4. Claims analysts upload claim document packets that include supporting materials such as claim forms, property damage pictures, identification documents, and audio files.

5. An Amazon Step Functions (Claims Processing) workflow processes the submitted documents using the Amazon BDA blueprints published in step 2 to extract data.

6. The automated process stores extracted insights from text documents, audio files, and image metadata in Amazon DynamoDB.

7. A computer vision model hosted on Amazon SageMaker AI endpoints processes the submitted images to detect tampering, and stores the results in Amazon DynamoDB.The computer vision model, using Error Level Analysis (ELA) as a straightforward image forgery detection technique that works by examining compression differences across image regions.It effectively reveals tampering by highlighting areas where compression levels don't match, making manipulated sections visually obvious even to non-experts. ELA's main advantage is that it requires only the questioned image itself, works with common image formats, and needs no specialized equipment or original image for comparison. Refer blog https://aws.amazon.com/blogs/machine-learning/train-and-host-a-computer-vision-model-for-tampering-detection-on-amazon-sagemaker-part-2/

8. Amazon Bedrock’s Nova Pro/Lite Foundational Model analyzes the data stored in Amazon DynamoDB to generate summary reports, which users can view in the web client.

9. Amazon Bedrock processes the insights to generate customized reports for claims analysts or trigger automated notifications through Amazon Simple Notification Service (Amazon SNS) via Email Notification.


## Next Steps
The solution streamlines the initial review process through automated completeness and validity checks, while generating custom blueprints for preliminary reports without requiring specialized ML expertise. BDA seamlessly integrates with existing fraud detection models on Amazon Sagemaker, incorporating sophisticated document tampering detection that analyzes multiple authentication factors including JPEG compression artifacts, edge inconsistencies, and EXIF metadata. 

The plug-and-play nature of BDA enables organizations to easily tailor output requirements for diverse business needs and downstream system integration.

## Cleanup
1. Destory CDK stacks

```bash
$ cdk destroy --all
```
2. Delete SageMaker Endpoint

```bash
$ aws sagemaker delete-endpoint --endpoint-name document-tampering-detection-v-DEMO
```

3. Delete Bedrock Data Automation Project

```bash
$ aws bedrock-data-automation delete-data-automation-project --project-arn <Project ARN created from above steps>
```

#### CDK Guideline
This repository includes a project for CDK development with Python.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the `.venv`
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.


#### Repository Structure
* insurance_claim_process_cdk
A CDK project to deploy AWS resources of the solution excluding Amazon Bedrock Automation project and blueprints.

* bedrock_data_automation
Code to create a BDA project and blueprints.

* sagemaker/document-tampering-detection
Contains code and image files to train and deploy a ML model to SageMaker Endpoint. The model is based on [AWS Machine Learning Blog](https://aws.amazon.com/blogs/machine-learning/train-and-host-a-computer-vision-model-for-tampering-detection-on-amazon-sagemaker-part-2/).

* frontend
React.js application for a frontend web page.

