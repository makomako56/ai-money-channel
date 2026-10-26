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

def sid(spk, sty):
    for s in speakers:
        if s["name"] == spk:
            for st in s["styles"]:
                if st["name"] == sty:
                    return st["id"]
    raise SystemExit(f"not found: {spk} {sty}")

TEXT = [
    ("h", "先生っ！AIって、結局…だれが一番儲かってるんですか？"),
    ("m", "ふふ、いい質問ですね。じゃあ、お金の流れで考えてみましょうか。"),
    ("h", "うっ…出た、お金の流れ…。"),
    ("m", "ゴールドラッシュで、一番儲かったのは…金を掘った人じゃなくて、スコップを売った人なんです。"),
]
PAIRS = [
    ("比較3_AivisSpeech_ひなた=まお_ミライ=まお(おちつき)", ("まお", "ノーマル"), ("まお", "おちつき")),
    ("比較4_AivisSpeech_ひなた=まお_ミライ=コハク", ("まお", "ノーマル"), ("コハク", "ノーマル")),
    ("比較5_AivisSpeech_ひなた=コハク_ミライ=まお(おちつき)", ("コハク", "ノーマル"), ("まお", "おちつき")),
]
sil = os.path.join(OUT, "sil.wav")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-t", "0.35", "-i", "anullsrc=r=44100:cl=mono", sil], check=True)
for title, h, m in PAIRS:
    parts = []
    for i, (who, text) in enumerate(TEXT):
        s_id = sid(*(h if who == "h" else m))
        q = json.loads(call("/audio_query?" + urllib.parse.urlencode({"text": text, "speaker": s_id}), method="POST"))
        wav = call(f"/synthesis?speaker={s_id}", json.dumps(q).encode(), "POST")
        p = os.path.join(OUT, f"part{i}.wav"); open(p, "wb").write(wav); parts.append(p)
    lst = os.path.join(OUT, "list.txt")
    with open(lst, "w") as f:
        for p in parts: f.write(f"file '{os.path.abspath(p)}'\nfile '{os.path.abspath(sil)}'\n")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst, "-ar", "44100", "-ac", "1", "-b:a", "160k", os.path.join(OUT, title + ".mp3")], check=True)
    for p in parts + [lst]: os.remove(p)
    print("done", title)
os.remove(sil)
print("done", name)
