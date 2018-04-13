Home Assistant - Housie
Welcome!

This Alexa skill contain lambda code and config file.

You should have some experience python 3.6
Skill also requires boto3 package.
	Command : pip install boto3

Step1 : Provide skill name, invocation name.
Step2 : Add the json file in SpeechAssets folder, to build interaction model.
Step3 : Login to your aws console, create a lambda function.
Step4 : Zip the boto3 package, config.py and lambda_handler.py , upload it to lambda.
Step5 : Copy the arn of your lambda code and add the arn as endpoint in skill.
Step6 : Fill the details for launch in alexa skill.

