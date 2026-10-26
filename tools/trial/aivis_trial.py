"""AivisSpeech の試聴サンプルを作る一時ツール（Claude作成・声の選定後に削除）。"""
import json, os, subprocess, sys, urllib.parse, urllib.request
B = os.environ.get("ENGINE", "http://127.0.0.1:10101")
OUT = sys.argv[1]
os.makedirs(OUT, exist_ok=True)

def call(path, data=None, method="GET"):
    req = urllib.request.Request(B + path, data=data, method=method, headers={"Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=300).read()

speakers = json.loads(call("/speakers"))
lines_out = []
for s in speakers:
    lines_out.append(f"{s['name']}: " + ", ".join(f"{st['name']}={st['id']}" for st in s["styles"]))
open(os.path.join(OUT, "voices.txt"), "w").write("\n".join(lines_out))
print("\n".join(lines_out))

def style(name_part):
    for s in speakers:
        for st in s["styles"]:
            if name_part in st["name"]:
                return st["id"], f"{s['name']}_{st['name']}"
    st = speakers[0]["styles"][0]
    return st["id"], f"{speakers[0]['name']}_{st['name']}"

calm, calm_name = style("落ち着き")
high, high_name = style("テンション")
dialogue = [
    (high, "先生っ！AIって、結局…だれが一番儲かってるんですか？"),
    (calm, "ふふ、いい質問ですね。じゃあ、お金の流れで考えてみましょうか。"),
    (high, "うっ…出た、お金の流れ…。"),
    (calm, "ゴールドラッシュで、一番儲かったのは…金を掘った人じゃなくて、スコップを売った人なんです。"),
]
parts = []
for i, (sid, text) in enumerate(dialogue):
    q = json.loads(call("/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": sid}), method="POST"))
    wav = call(f"/synthesis?speaker={sid}", json.dumps(q).encode(), "POST")
    p = os.path.join(OUT, f"part{i}.wav"); open(p, "wb").write(wav); parts.append(p)
sil = os.path.join(OUT, "sil.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-t", "0.35", "-i", "anullsrc=r=44100:cl=mono", sil], check=True)
lst = os.path.join(OUT, "list.txt")
with open(lst, "w") as f:
    for p in parts: f.write(f"file '{os.path.abspath(p)}'\nfile '{os.path.abspath(sil)}'\n")
name = f"比較3_AivisSpeech_ひなた={high_name}_ミライ={calm_name}.mp3"
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-ar", "44100", "-ac", "1", "-b:a", "160k", os.path.join(OUT, name)], check=True)
for p in parts + [sil, lst]: os.remove(p)
print("done", name)
