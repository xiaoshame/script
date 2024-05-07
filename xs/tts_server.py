from fastapi import FastAPI,Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from speech_synthesis import tts
import os
import uvicorn

# class TTSRequest(BaseModel):
#     voice_id: str  # 假设voice_id是一个整数
#     text: str      # text是一个字符串

app = FastAPI()

# @app.get("/tts/")
# async def handle_tts(request: TTSRequest):
#     text_to_speech = tts()
#     audio_file_path,speech_synthesis_result = text_to_speech.speak(request.voice_id, request.text)

#     if os.path.isfile(audio_file_path):
#         # 使用 FileResponse 返回文件内容
#         return FileResponse(audio_file_path, filename="output.wav", media_type="audio/wav")
#     else:
#         print("audio_file_path: " + audio_file_path)
#         print(speech_synthesis_result)
#         return {"error": "File not found"}, 404

@app.get("/tts/")
async def handle_tts(voice_id: str = Query(None, description="The ID of the voice to use"),
                     text: str = Query(None, description="The text to be synthesized")):
    text_to_speech = tts()
    audio_file_path,speech_synthesis_result = text_to_speech.speak(voice_id, text)

    if os.path.isfile(audio_file_path):
        # 使用 FileResponse 返回文件内容
        return FileResponse(audio_file_path, filename="output.wav", media_type="audio/wav")
    else:
        print("audio_file_path: " + audio_file_path)
        print(speech_synthesis_result)
        return {"error": "File not found"}, 404

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

