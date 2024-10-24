from openai import OpenAI
client = OpenAI()

audio_file= open("/Users/daudahmed/project/IdeaStream/recordings/fb2a4600-d9cc-496f-beec-e6c57e4d8b5e_1729777243.wav", "rb")
translation = client.audio.translations.create(
  model="whisper-1", 
  file=audio_file
)
print(translation.text)