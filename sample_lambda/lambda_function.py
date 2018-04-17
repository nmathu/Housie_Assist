from __future__ import print_function
from config import *
import boto3
from boto3.dynamodb.conditions import Key, Attr

#Dynamodb
client = boto3.resource('dynamodb',aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key,region_name=region_name)
RecordedMessageTable=client.Table(table_name)

# We'll start with a couple of globals...
CardTitlePrefix = "Home Assistant - Housie"
		# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(output_speech,output_content, reprompt_text,should_end_session):
    """
    Build a speechlet JSON representation of the title, output text, 
    reprompt text & end of session
    """
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output_speech
        },
        'card': {
            'type': 'Standard',
            'title': CardTitlePrefix,
            'text': output_content,
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    """
    Build the full response JSON from the speechlet response
    """
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
# --------------- Functions that control the skill's behavior ------------------
	
def on_launch_response():#play auto_intro
	speech_output = "You can ask to record message or read message"
	speech_content = "Say 'Record Message' to start recording, 'Read Message' to read recorded message"
	# If the user either does not reply to the welcome message or says something
	# that is not understood, they will be prompted again with this text.
	reprompt_text = "How may I help you ?"
	should_end_session = False
	return build_response({}, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))
    
def handle_help():
	
	instruction='If you want to record message to someone, you can say "record message" after launching the skill. '
	instruction+='Mention the name of the person you want to send message to when Alexa asks, "whom is this message for". '
	instruction+='Say your message. Alexa will save you message and read it for you. '
	instruction+='To hear message recorded for you, say "read message". '
	instruction+='Provide your name when Alexa asks you, "what is you name". '
	instruction+='Do you want to record message or read message'
	
	speech_output = instruction
	speech_content = instruction
	reprompt_text="Do you want to record message or read message."
	should_end_session = False
	return build_response({}, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

def handle_invalid_intent():
	speech_output = 'I am unable to understand you.'
	speech_content = "Unable to understand. Try again"
	# Setting this to true ends the session and exits the skill.
	should_end_session = True
	return build_response({}, build_speechlet_response(speech_output,speech_content, None, should_end_session))

def handle_session_end_request():
	speech_output = 'Ok Bye!'
	speech_content = "Bye!"
	# Setting this to true ends the session and exits the skill.
	should_end_session = True
	return build_response({}, build_speechlet_response(speech_output,speech_content, None, should_end_session))

#------------------------------------message recording functions--------------------
def start_record(session,slots):
	if 'value' in slots['reciever_name']:
		return save_name_for_recording(session,slots)
	else:
		attributes=session['attributes']
		attributes['message_context']="context_record_message"
		speech_output = 'whom is this message for?'
		speech_content = "Whom is this message for?"
		reprompt_text = "please mention the name of receiver"
		# Setting this to true ends the session and exits the skill.
		should_end_session = False
		return build_response(attributes, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

def save_name_for_recording(session,slots):
	attributes=session['attributes']
	if('value' in slots['reciever_name']):
		attributes['reciever_name']=slots['reciever_name']['value']
		speech_output = "tell me your message"
		speech_content = "Tell me your message."
		reprompt_text ="your recording has started."
	else:
		attributes['reciever_name']=slots['reciever_name']['value']
		speech_output = "Name not received.Tell me who is this message for"
		speech_content = "Name not received. Please provide name"
		reprompt_text ="Name not received"
	# Setting this to true ends the session and exits the skill.
	should_end_session = False
	return build_response(attributes, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))
	
def record_message(session,slots):#Function to check if the slot has value or request is valid
	attributes=session['attributes']
	if('value' in slots['your_message']):	#If some request is placed
		if 'reciever_name' in session['attributes']:
			attributes['record_message']=slots['your_message']['value']
			speech_output = "your message is "+slots['your_message']['value']+". Is there anything else you want me to do?"
			speech_content = "Your message is "+slots['your_message']['value']+" . Is there anything else you want me to do?'"
			response=RecordedMessageTable.put_item(
				Item={
					'message_id':session['attributes']['reciever_name']+slots['your_message']['value'],
					'UserID':session['user']['userId'],
					'Name':session['attributes']['reciever_name'],
					'Message':slots['your_message']['value']
				})
		else:
			speech_output = "Sorry I don't know that. Do you want to continue?"
			speech_content = "Sorry I don't know that. Do you want to continue?"	
	else:
		speech_output = "your message was not recorded. Do you want to continue"
		speech_content = "Your message was not recorded. Do you want to continue?"
	# Setting this to true ends the session and exits the skill.
	reprompt_text="Is there anything else you want me to do?"
	should_end_session = False
	return build_response(attributes, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

def stop_record(session):
	if 'record_message' in session['attributes'] and 'reciever_name' in session['attributes'] :
		print(session['attributes']['reciever_name'])
		print(session['attributes']['record_message'])
		response=RecordedMessageTable.put_item(
			Item={
				'messageID':session['attributes']['reciever_name']+session['attributes']['record_message'],
				'UserID':session['user']['userId'],
				'Name':session['attributes']['reciever_name'],
				'Message':session['attributes']['record_message']
			})
		print(response)
		speech_output = "Message saved. Is there anything else you want me to do"
		speech_content = "Message saved. Is there anything else you want me to do"
		reprompt_text ="Message saved. Is there anything else you want me to do"
	else:
		speech_output = "Couldn't record message.Do you want record message or read message?"
		speech_content = "Couldn't record message. Do you want record message or read message?"
		reprompt_text ="Couldn't record message. Please try again. Do you want to record another message"
	# Setting this to true ends the session and exits the skill.
	should_end_session = False
	return build_response({}, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

#-------------------------------------message retrieval functions-------------------------

def get_message(session,slots):
	if 'value' in slots['reciever_name']:
		return save_name_for_retrival(session,slots)
	else:
		attributes=session['attributes']
		attributes['message_context']='context_read_message'
		speech_output = 'what is your name?'
		speech_content = "What is your name?"
		reprompt_text = "what is your name? I require your name to provide you messages"
		should_end_session = False
		return build_response(attributes, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

def save_name_for_retrival(session,slots):
	attributes=session['attributes']
	if('value' in slots['reciever_name'] or 'reciever_name' in session['attributes']):
		attributes['reciever_name']=slots['reciever_name']['value']
		message = fetch_message(slots['reciever_name']['value'],session['user']['userId'])
		speech_output = message+". Do you want repeat message or delete message?"
		speech_content = message+". Do you want repeat message or delete message?"
		reprompt_text ="Do you want to repeat message or delete message"
		should_end_session = False
	else:
		attributes['reciever_name']=slots['reciever_name']['value']
		speech_output = "Name not received. please provide name"
		speech_content = "Name not received"
		reprompt_text ="Name not received"
		should_end_session = False
	return build_response(attributes, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

def repeat_message(session):
	message = fetch_message(session['attributes']['reciever_name'],session['user']['userId'])
	speech_output = message+". Do you want repeat message or delete message?"
	speech_content = message+". Do you want repeat message or delete message?"
	reprompt_text ="Do you want to repeat message or delete message"
	should_end_session = False
	return build_response(session, build_speechlet_response(speech_output,speech_content, reprompt_text, should_end_session))

def fetch_message(name,user_id):
	response=RecordedMessageTable.scan(
        FilterExpression=Key('Name').eq(name)
    )
	message=response['Items']
	print("db response is--------")
	message_str = "your message is,"
	for item in message:
		if item['UserID'] == user_id:
			message_str+=str(item['Message'])+". "
	if message_str:
		return message_str
	else:
		return ("You don't have any messages")

def delete_message(session):
	response_scan=RecordedMessageTable.scan(
		FilterExpression=Key('Name').eq(session['attributes']['reciever_name'])
	)
	message=response_scan['Items']
	for item in message:
		response = RecordedMessageTable.delete_item(
				Key={
						'message_id': session['attributes']['reciever_name']+str(item['Message'])
				}
				)
	speech_output = 'Your messages are deleted'
	speech_content = "Your messages are deleted"
	# Setting this to true ends the session and exits the skill.
	should_end_session = True
	return build_response({}, build_speechlet_response(speech_output,speech_content, None, should_end_session))
	
# --------------- Events ------------------
def on_session_started(session_started_request, session):
    """ Called when the session starts """
    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])
def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they want """
    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    session['attributes']={}
    return on_launch_response()
	
def on_intent(intent_request, session):
	""" Called when the user specifies an intent for this skill """
	print("on_intent requestId=" + intent_request['requestId'] +
			", sessionId=" + session['sessionId'])
	if 'attributes' not in session.keys():
		session['attributes'] = {}
	print(session['attributes'])	
	intent = intent_request['intent']
	intent_name = intent_request['intent']['name']
	# Dispatch to your skill's intent handlers
	if intent_name == "RecordStartIntent":
		return start_record(session,intent['slots'])
	if intent_name == "GetNameIntent":
		if session['attributes']['message_context'] == 'context_record_message':
			return save_name_for_recording(session,intent['slots'])
		else:
			return save_name_for_retrival(session,intent['slots'])
	if intent_name == "RecordMessageIntent":
		return record_message(session,intent['slots'])
	if intent_name == "RecordStopIntent":
		return stop_record(session)
	if intent_name == "GetMessageIntent":
		return get_message(session,intent['slots'])
	if intent_name == "RepeatIntent":
		return repeat_message(session)
	if intent_name == "DeleteIntent":
		return delete_message(session)
	if intent_name == "AMAZON.YesIntent":
		return on_launch_response()
	if intent_name == "AMAZON.NoIntent":
		return handle_session_end_request()
	if intent_name ==  "AMAZON.HelpIntent":
		return handle_help()
	if (intent_name == "AMAZON.StopIntent" or intent_name == "AMAZON.CancelIntent"):
		return handle_session_end_request()
	else:
		return handle_invalid_intent()

def on_session_ended(session_ended_request, session):
	""" Called when the user ends the session. Is not called when the skill returns should_end_session=true """
	print("on_session_ended requestId=" + session_ended_request['requestId'] +
		", sessionId=" + session['sessionId'])
# --------------- Main handler ------------------
def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    if('session' in event):
        print("event.session.application.applicationId=" +
              event['session']['application']['applicationId'])
        if event['session']['new']:
            on_session_started({'requestId': event['request']['requestId']},
                               event['session'])
    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])