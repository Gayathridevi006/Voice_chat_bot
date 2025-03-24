import os
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client
import openai
from flask import Flask, request
from google.cloud import speech, texttospeech


openai.api_key = os.getenv("OPENAI_API_KEY")
twilio_client = Client(os.getenv("TWILIO_ACCOUNT_SID"), os.getenv("TWILIO_AUTH_TOKEN"))

app = Flask(__name__)


speech_client = speech.SpeechClient()
tts_client = texttospeech.TextToSpeechClient()


def ai_conversation(user_input):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful AI salesperson who can make deals."},
                  {"role": "user", "content": user_input}]
    )
    return response['choices'][0]['message']['content']


def text_to_speech(text):
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(language_code="en-US", ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL)
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

    response = tts_client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
    return response.audio_content


@app.route("/incoming_call", methods=["POST"])
def incoming_call():
    response = VoiceResponse()
    gather = Gather(input="speech", timeout=5, speechTimeout="auto", action="/process_response")
    gather.say("Hello, I am your AI assistant. How can I assist you today?")
    response.append(gather)

    return str(response)

# Process Caller Response
@app.route("/process_response", methods=["POST"])
def process_response():
    user_speech = request.form.get("SpeechResult")
    ai_reply = ai_conversation(user_speech)

    response = VoiceResponse()
    if "cannot proceed" in ai_reply.lower():  # If AI can't handle the deal, transfer to agent
        response.say("I will transfer you to a human agent.")
        response.dial("+agent_phone_number")  # Replace with the actual agent number
    else:
        response.say(ai_reply)

    return str(response)

# Make an Outgoing Call
def make_call(client_phone):
    call = twilio_client.calls.create(
        to=client_phone,
        from_=os.getenv("TWILIO_PHONE_NUMBER"),
        url="http://your-server.com/incoming_call"
    )
    return call.sid

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
