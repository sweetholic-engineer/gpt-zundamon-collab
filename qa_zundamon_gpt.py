### 音声入力（whisper）
import whisper, os
import sounddevice as sd 
import scipy.io.wavfile
### 音声再生
import requests, playsound
### GPT
from openai import OpenAI
### その他
import re, time
from datetime import datetime, timedelta

### 音声ファイルの一時置き場
script_dir = os.getcwd()
tmp_kwfile = script_dir + "/voices/keyword.wav"
tmp_inputfile = script_dir + "/voices/input.wav"
tmp_outputfile = script_dir + "/voices/output.wav"

### OpenAI API Key
client = OpenAI(
    api_key = "sk-proj-XXXXXXX",
)

### whisper model
whisper_model = whisper.load_model("small")

def ask_chatgpt( text ):
    # GPTに質問（回答をずんだもんっぽく）
    res = client.responses.create(
        model = "gpt-4.1",
        input = text + "。回答の語尾は「なのだ」。なるべく簡潔に答えて。",
    )
    return res.output_text

def transcribe( filename=tmp_inputfile ):
    return whisper_model.transcribe( filename, fp16=False )["text"]    

def normalize_phrase( text ):
    today = datetime.now()
    # 日付はyyyy年mm月dd日の形に変更
    replacements = {
        "明日": (today + timedelta(days=1)).strftime("%Y年%m月%d日"),
        "今日": today.strftime("%Y年%m月%d日"),
        "明後日": (today + timedelta(days=2)).strftime("%Y年%m月%d日"),
    }
    for k, v in replacements.items(): text = re.sub(k, v, text)
    return text

def zundamon_voice(text, speaker_id=3):
    base_url = "http://localhost:50021"

    # 音声合成用のクエリ作成
    query = requests.post(f"{base_url}/audio_query", params={"text": text, "speaker": speaker_id})
    query_json = query.json()

    # 音声合成
    audio = requests.post(f"{base_url}/synthesis", params={"speaker": speaker_id}, json=query_json)

    with open(tmp_outputfile, "wb") as fp:
        fp.write(audio.content)

    playsound.playsound(tmp_outputfile)

def record_audio(filename=tmp_inputfile, duration=5, fs=16000):
    # 5秒間で音声録音
    audio = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
    sd.wait()

    # 音声を一旦出力
    scipy.io.wavfile.write(filename, fs, audio)

def main():
    print("Waiting for Keyword...")
    while True:
        record_audio(filename=tmp_kwfile, duration=2)
        keyword = transcribe(filename=tmp_kwfile).lower()
        
        print (keyword)
        if "もしもし" in keyword:
            print("Start Recording")
            record_audio()
            input_text = transcribe()
            print("audio recognition result : ", input_text)

            que_normalize = normalize_phrase( input_text )
            gpt_ans = ask_chatgpt( que_normalize )

            zundamon_voice( gpt_ans )
            break

if __name__ == '__main__':
    main()