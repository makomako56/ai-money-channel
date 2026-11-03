"""Render a 1280x720 episode thumbnail from thumbnail.json with Playwright."""
import argparse
import json
import re
import struct
import subprocess
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import yaml

ROOT = Path(__file__).resolve().parent.parent
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
MAX_BYTES = 2_000_000
WIDTH, HEIGHT = 1280, 720
REQUIRED_FIELDS = {"main_text", "sub_text", "character", "expression", "accent"}
OPTIONAL_FIELDS = {"sub_character", "sub_expression"}
V3_FIELDS = {"lines", "characters"}
COLOR = re.compile(r"#[0-9a-fA-F]{6}\Z")
EPISODE = re.compile(r"ep[0-9]+_[\w-]+\Z")
FACE_AREAS = {
    "mirai": [95, 25, 245, 215],
    "hinata": [90, 20, 250, 210],
}


def asset_url(root, relative):
    if not isinstance(relative, str):
        raise ValueError("素材のファイル名が不正です")
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"素材のパスが不正です: {relative}")
    absolute = (root / path).resolve()
    if not absolute.is_relative_to(root.resolve()) or not absolute.is_file():
        raise ValueError(f"素材がありません: {relative}")
    return "/" + path.as_posix()


def validate_input(data, characters, style, root=ROOT):
    if (not isinstance(data, dict) or not REQUIRED_FIELDS.issubset(data) or
            not set(data).issubset(REQUIRED_FIELDS | OPTIONAL_FIELDS | V3_FIELDS)):
        raise ValueError("thumbnail.json には main_text、sub_text、character、expression、accent が必要です")
    if ("sub_character" in data) != ("sub_expression" in data):
        raise ValueError("sub_character と sub_expression は両方指定してください")
    main = data["main_text"]
    if not isinstance(main, str) or "\r" in main:
        raise ValueError("main_text は1〜2行の文字列が必要です")
    lines = main.split("\n")
    if not 1 <= len(lines) <= 2 or any(not 1 <= len(line.strip()) <= 10 or line != line.strip() for line in lines):
        raise ValueError("main_text は1〜2行、各行1〜10文字で指定してください")
    sub = data["sub_text"]
    if not isinstance(sub, str) or not 1 <= len(sub) <= 18 or sub != sub.strip() or "\n" in sub:
        raise ValueError("sub_text は1〜18文字の1行で指定してください")
    accent = data["accent"]
    if not isinstance(accent, str) or not COLOR.fullmatch(accent):
        raise ValueError("accent は #RRGGBB 形式が必要です")
    character = data["character"]
    if not isinstance(character, str) or character not in ("mirai", "hinata") or character not in characters:
        raise ValueError(f"未定義のキャラです: {character}")
    expression = data["expression"]
    images = characters[character].get("expressions", {})
    if not isinstance(expression, str) or expression not in images or not isinstance(images[expression], str):
        raise ValueError(f"未定義の表情または画像です: {expression}")
    image_name = images[expression]
    if Path(image_name).name != image_name or not image_name.endswith(".png"):
        raise ValueError("キャラ画像名が不正です")
    image_url = asset_url(root, f"assets/characters/{character}/transparent/{image_name}")
    sub_image_url = None
    if "sub_character" in data:
        sub_character = data["sub_character"]
        if (not isinstance(sub_character, str) or sub_character not in ("mirai", "hinata") or
                sub_character not in characters or sub_character == character):
            raise ValueError(f"未定義またはメインと同じサブキャラです: {sub_character}")
        sub_expression = data["sub_expression"]
        sub_images = characters[sub_character].get("expressions", {})
        if (not isinstance(sub_expression, str) or sub_expression not in sub_images or
                not isinstance(sub_images[sub_expression], str)):
            raise ValueError(f"未定義のサブキャラ表情または画像です: {sub_expression}")
        sub_image_name = sub_images[sub_expression]
        if Path(sub_image_name).name != sub_image_name or not sub_image_name.endswith(".png"):
            raise ValueError("サブキャラ画像名が不正です")
        sub_image_url = asset_url(
            root, f"assets/characters/{sub_character}/transparent/{sub_image_name}")
    has_v3_lines = "lines" in data
    has_v3_characters = "characters" in data
    if has_v3_lines != has_v3_characters:
        raise ValueError("v3 の lines と characters は両方指定してください")
    v3_lines = None
    character_urls = [image_url]
    character_faces = [FACE_AREAS[character]]
    if sub_image_url:
        character_urls.append(sub_image_url)
        character_faces.append(FACE_AREAS[data["sub_character"]])
    else:
        # v3 thumbnails always show both people. Keep old thumbnail.json files
        # compatible by supplying the other character's default expression.
        partner = "hinata" if character != "hinata" else "mirai"
        partner_images = characters.get(partner, {}).get("expressions", {})
        partner_image = partner_images.get("通常")
        if not isinstance(partner_image, str):
            raise ValueError(f"既定の表情がありません: {partner}")
        if Path(partner_image).name != partner_image or not partner_image.endswith(".png"):
            raise ValueError("既定のキャラ画像名が不正です")
        character_urls.append(asset_url(
            root, f"assets/characters/{partner}/transparent/{partner_image}"))
        character_faces.append(FACE_AREAS[partner])
    if has_v3_lines:
        raw_lines = data["lines"]
        if not isinstance(raw_lines, list) or not 3 <= len(raw_lines) <= 4:
            raise ValueError("lines は3〜4段で指定してください")
        v3_lines = []
        for line in raw_lines:
            if not isinstance(line, dict) or set(line) != {"segments"}:
                raise ValueError("lines の各段には segments だけを指定してください")
            segments = line["segments"]
            if not isinstance(segments, list) or not 1 <= len(segments) <= 6:
                raise ValueError("各段の segments は1〜6個で指定してください")
            normalized = []
            total_length = 0
            for segment in segments:
                if (not isinstance(segment, dict) or "text" not in segment or
                        not set(segment).issubset({"text", "color"})):
                    raise ValueError("segment には text と任意の color を指定してください")
                text = segment["text"]
                color = segment.get("color")
                if (not isinstance(text, str) or not text or text != text.strip() or
                        "\n" in text or "\r" in text):
                    raise ValueError("segment の text は空白のない1行で指定してください")
                if color is not None and (not isinstance(color, str) or not COLOR.fullmatch(color)):
                    raise ValueError("segment の color は #RRGGBB 形式が必要です")
                total_length += len(text)
                normalized.append({"text": text, "color": color})
            if not 1 <= total_length <= 18:
                raise ValueError("各段の文字は合計1〜18文字で指定してください")
            v3_lines.append(normalized)

        specs = data["characters"]
        if not isinstance(specs, list) or len(specs) != 2:
            raise ValueError("characters は異なる2人を指定してください")
        character_urls = []
        character_faces = []
        names = []
        for spec in specs:
            if not isinstance(spec, dict) or set(spec) != {"character", "expression"}:
                raise ValueError("characters には character と expression を指定してください")
            name, face = spec["character"], spec["expression"]
            if not isinstance(name, str) or name not in ("mirai", "hinata") or name not in characters:
                raise ValueError(f"未定義のキャラです: {name}")
            images = characters[name].get("expressions", {})
            if not isinstance(face, str) or face not in images or not isinstance(images[face], str):
                raise ValueError(f"未定義の表情または画像です: {face}")
            image_name = images[face]
            if Path(image_name).name != image_name or not image_name.endswith(".png"):
                raise ValueError("キャラ画像名が不正です")
            names.append(name)
            character_urls.append(asset_url(
                root, f"assets/characters/{name}/transparent/{image_name}"))
            character_faces.append(FACE_AREAS[name])
        if len(set(names)) != 2:
            raise ValueError("characters は異なる2人を指定してください")
    if not isinstance(style, dict) or not isinstance(style.get("font_file"), str):
        raise ValueError("thumbnail_style.yaml の font_file が必要です")
    font_url = asset_url(root, style["font_file"])
    if not font_url.endswith(".woff2"):
        raise ValueError("サムネのフォントは woff2 が必要です")
    colors, layout = style.get("colors"), style.get("layout")
    color_keys = ("background_top", "background_bottom", "text", "stroke")
    layout_keys = ("text_x", "main_y", "sub_y", "text_width", "main_font_max",
                   "main_font_min", "sub_font_size", "character_width",
                   "character_right", "character_bottom", "sub_character_width",
                   "sub_character_right", "sub_character_bottom")
    if not isinstance(colors, dict) or any(not isinstance(colors.get(key), str) or
                                            not COLOR.fullmatch(colors[key]) for key in color_keys):
        raise ValueError("thumbnail_style.yaml の colors が不正です")
    if not isinstance(layout, dict) or any(type(layout.get(key)) is not int or
                                            abs(layout[key]) > 2000 for key in layout_keys):
        raise ValueError("thumbnail_style.yaml の layout が不正です")
    if not 1 <= layout["main_font_min"] <= layout["main_font_max"] or not 1 <= layout["sub_font_size"]:
        raise ValueError("thumbnail_style.yaml の文字サイズが不正です")
    if (not 1 <= layout["text_width"] <= WIDTH or
            not 1 <= layout["character_width"] <= WIDTH or
            not 1 <= layout["sub_character_width"] <= WIDTH):
        raise ValueError("thumbnail_style.yaml の幅が不正です")
    return {"main_lines": lines, "sub_text": sub, "accent": accent,
            "image_url": image_url, "sub_image_url": sub_image_url, "font_url": font_url,
            "lines": v3_lines, "character_urls": character_urls,
            "character_faces": character_faces,
            "colors": {key: colors[key] for key in color_keys},
            "layout": {key: layout[key] for key in layout_keys}}


def verify_png(path):
    path = Path(path)
    size = path.stat().st_size
    if not 24 <= size < MAX_BYTES:
        raise ValueError(f"サムネ画像は2MB未満が必要です（{size} bytes）")
    with path.open("rb") as stream:
        header = stream.read(24)
    if header[:8] != PNG_SIGNATURE or header[12:16] != b"IHDR":
        raise ValueError("サムネ画像がPNGではありません")
    width, height = struct.unpack(">II", header[16:24])
    if (width, height) != (WIDTH, HEIGHT):
        raise ValueError(f"サムネ画像は1280x720が必要です（{width}x{height}）")


NODE_SCRIPT = r"""
const fs = require("fs");
const { chromium } = require("playwright");
(async () => {
  const [port, output] = process.argv.slice(1);
  const payload = JSON.parse(fs.readFileSync(0, "utf8"));
  const browser = await chromium.launch({headless:true});
  try {
    const context = await browser.newContext({viewport:{width:1280,height:720},deviceScaleFactor:1});
    const page = await context.newPage();
    await page.goto("http://127.0.0.1:" + port + "/", {waitUntil:"load"});
    await page.setContent(`<!doctype html><html lang="ja"><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}html,body{width:1280px;height:720px;overflow:hidden}
body{position:relative;font-family:Maru,sans-serif;font-weight:900;background:#24345c}
.card{position:absolute;left:14px;top:14px;width:1196px;height:692px;border-radius:26px;overflow:hidden;background:radial-gradient(ellipse 80% 90% at 70% 60%,#2b3f7a 0%,#141c3a 70%)}
.grid{position:absolute;inset:0;background:linear-gradient(rgba(120,170,255,.10) 2px,transparent 2px) 0 0/48px 48px,linear-gradient(90deg,rgba(120,170,255,.10) 2px,transparent 2px) 0 0/48px 48px}
.glow{position:absolute;right:-80px;bottom:-120px;width:760px;height:760px;border-radius:50%;background:radial-gradient(circle,rgba(255,170,60,.45),transparent 62%)}
.side{position:absolute;right:0;top:0;width:70px;height:720px;display:flex;align-items:center;justify-content:center}.side span{writing-mode:vertical-rl;color:#fff;font-size:30px;letter-spacing:.12em;white-space:nowrap}.side b{color:#ffb35c}
.character{position:absolute;filter:drop-shadow(4px 0 0 #fff) drop-shadow(-4px 0 0 #fff) drop-shadow(0 -4px 0 #fff) drop-shadow(0 10px 18px rgba(0,0,0,.5))}.main{left:826px;top:45px;height:800px}.sub-character{left:603px;top:273px;height:760px}
.box{position:absolute;left:30px;transform:skew(-7deg);white-space:nowrap;line-height:1;z-index:2}.box>span{display:inline-block;transform:skew(7deg)}
.b1{top:34px;background:#fff;padding:12px 24px 16px;font-size:66px;color:#141c3a;border-radius:6px}.b2{top:150px;padding:0 10px;font-size:130px;color:#fff;letter-spacing:-.05em;paint-order:stroke fill;-webkit-text-stroke:20px #141c3a;filter:drop-shadow(0 8px 0 #000)}
.b3{top:318px;font-size:150px;color:#fff;letter-spacing:-.05em;padding:0 10px;paint-order:stroke fill;-webkit-text-stroke:20px #141c3a;filter:drop-shadow(0 8px 0 #000)}.b4{top:540px;background:#141c3a;border:5px solid #fff;padding:12px 22px 16px;font-size:48px;color:#fff;border-radius:8px}.b4>span>span+span{margin-left:.25em}
</style><body><div class="card"><div class="grid"></div><div class="glow"></div><img id="person1" class="character main" alt=""><img id="person2" class="character sub-character" alt=""><div id="copy"></div></div><div class="side"><span>ミライ先生の<b>AI</b>マネー教室</span></div></body></html>`, {waitUntil:"load"});
    await page.evaluate(async data => {
      const font=new FontFace("Maru",'url("'+data.font_url+'")',{weight:"900"});
      document.fonts.add(await font.load());await document.fonts.ready;
      const fallback=[...data.main_lines.map(text=>[{text,color:null}]),[{text:data.sub_text,color:data.accent}]];
      const lines=data.lines || fallback;
      const copy=document.getElementById("copy");
      const classes=data.lines ? lines.map((_,index)=>"b"+(index+1)) :
        (data.main_lines.length===2 ? ["b1","b2","b4"] : ["b2","b4"]);
      lines.forEach((segments,index)=>{
        const box=document.createElement("div");box.className="box "+classes[index];
        const row=document.createElement("span");
        segments.forEach(segment=>{const span=document.createElement("span");span.textContent=segment.text;if(segment.color)span.style.color=segment.color;row.appendChild(span)});
        box.appendChild(row);copy.appendChild(box);
      });
      const people=data.character_urls;
      for(let i=0;i<2;i++){
        const image=document.getElementById("person"+(i+1));
        if(people[i]){image.src=people[i];await image.decode()}else{image.hidden=true}
      }
      await new Promise(resolve=>requestAnimationFrame(()=>resolve()));
      const faces=[...document.querySelectorAll(".character:not([hidden])")].map((image,index)=>{
        const rect=image.getBoundingClientRect(),scale=rect.height/image.naturalHeight;
        const [left,top,right,bottom]=data.character_faces[index];
        return {name:image.className,x1:rect.left+left*scale,y1:rect.top+top*scale,
          x2:rect.left+right*scale,y2:rect.top+bottom*scale};
      });
      const intersects=(a,b)=>a.x1<b.x2&&b.x1<a.x2&&a.y1<b.y2&&b.y1<a.y2;
      const bounds=document.querySelector(".card").getBoundingClientRect();
      const boxRect=box=>{const rect=box.getBoundingClientRect();return {
        name:box.textContent,x1:rect.left,y1:rect.top,x2:rect.right,y2:rect.bottom};};
      const minimum={b1:36,b2:56,b3:56,b4:28};
      [...document.querySelectorAll(".box")].forEach(box=>{
        const kind=[...box.classList].find(name=>minimum[name]);
        let size=parseFloat(getComputedStyle(box).fontSize);
        let rect=boxRect(box);
        while((rect.x2>bounds.right-20 || faces.some(face=>intersects(face,rect))) && size>minimum[kind]){
          size=Math.max(minimum[kind],size-2);box.style.fontSize=size+"px";rect=boxRect(box);
        }
      });
      const boxes=[...document.querySelectorAll(".box")].map(box=>{
        const rect=box.getBoundingClientRect();
        return {name:box.textContent,x1:rect.left,y1:rect.top,x2:rect.right,y2:rect.bottom};
      });
      const overflow=boxes.filter(box=>box.x1<bounds.left || box.x2>bounds.right-20);
      if(overflow.length)throw new Error("文字のはみ出しを検出: "+overflow.map(box=>box.name).join(", "));
      const overlaps=[];
      faces.forEach((face,index)=>{
        faces.slice(index+1).forEach(other=>intersects(face,other)&&overlaps.push(face.name+" × "+other.name));
        boxes.forEach(box=>intersects(face,box)&&overlaps.push(face.name+" × "+box.name));
      });
      window.__overlaps=overlaps;
      if(overlaps.length)throw new Error("顔の重なりを検出: "+overlaps.join(", "));
    }, payload);
    await page.screenshot({path:output,type:"png",animations:"disabled"});
    await context.close();
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error.stack || error); process.exit(1); });
"""


def render(payload, output):
    class QuietHandler(SimpleHTTPRequestHandler):
        def log_message(self, *_):
            pass

    handler = partial(QuietHandler, directory=str(ROOT))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        result = subprocess.run(
            ["node", "-e", NODE_SCRIPT, str(server.server_address[1]), str(output)],
            input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True,
            cwd=ROOT, timeout=120)
        if result.returncode:
            raise RuntimeError("Playwrightのサムネ撮影に失敗: " + result.stderr[-2000:])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--episode", required=True)
    args = parser.parse_args()
    if not EPISODE.fullmatch(args.episode):
        parser.error("episode の形式が不正です")
    episode = ROOT / "episodes" / args.episode
    output = ROOT / "output" / args.episode / "thumbnail"
    try:
        if episode.is_symlink() or not episode.is_dir():
            raise ValueError(f"エピソードがありません: {args.episode}")
        if output.exists():
            raise ValueError(f"出力先が既にあります: {output}")
        data = json.loads((episode / "thumbnail.json").read_text(encoding="utf-8"))
        characters = yaml.safe_load((ROOT / "config/characters.yaml").read_text(encoding="utf-8"))
        style = yaml.safe_load((ROOT / "config/thumbnail_style.yaml").read_text(encoding="utf-8"))
        payload = validate_input(data, characters, style)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent, prefix=".thumbnail-") as temporary:
            staging = Path(temporary) / "thumbnail"
            staging.mkdir()
            image = staging / "thumbnail.png"
            render(payload, image)
            verify_png(image)
            staging.rename(output)
        print(f"サムネ完成: {output / 'thumbnail.png'}")
    except (OSError, ValueError, TypeError, KeyError, RuntimeError, subprocess.TimeoutExpired,
            json.JSONDecodeError, yaml.YAMLError) as exc:
        parser.exit(1, f"ERROR: {exc}\n")


if __name__ == "__main__":
    main()
