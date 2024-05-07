from fastapi import FastAPI,Query
from fastapi.responses import FileResponse,StreamingResponse
from pydantic import BaseModel
from azure_speech_synthesis import AzureTTs
from ali_speech_synthesis import AliTTs
import os
import io
import uvicorn

app = FastAPI()

@app.get("/azure_tts/")
async def azure_tts(voice_id: str = Query(None, description="The ID of the voice to use"),
                     text: str = Query(None, description="The text to be synthesized")):
    text_to_speech = AzureTTs()
    audio_file_path,speech_synthesis_result = text_to_speech.speak(voice_id, text)

    if os.path.isfile(audio_file_path):
        # 使用 FileResponse 返回文件内容
        return FileResponse(audio_file_path, filename="output.wav", media_type="audio/wav")
    else:
        print("audio_file_path: " + audio_file_path)
        print(speech_synthesis_result)
        return {"error": "File not found"}, 404

@app.get("/ali_tts/")
async def ali_tts(voice_id: str = Query(None, description="The ID of the voice to use"),
                     text: str = Query(None, description="The text to be synthesized")):
    text_to_speech = AliTTs()
    audio_file_path = text_to_speech.speak(voice_id, text)
    if os.path.isfile(audio_file_path):
        # 使用 FileResponse 返回文件内容
        return FileResponse(audio_file_path, filename="output.wav", media_type="audio/wav")
    else:
        return {"error": "File not found"}, 404

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

