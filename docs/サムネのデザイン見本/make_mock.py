# サムネのデザイン見本（6案）を HTML で作り、PNG に描画する
import pathlib, asyncio
from PIL import Image
from playwright.async_api import async_playwright

REPO = pathlib.Path('/home/claude/ai-money-channel')
OUT = pathlib.Path(__file__).parent
CH = REPO / 'assets/characters'
FONT = (REPO / 'assets/fonts/zen-maru-gothic-japanese-900-normal.woff2').as_uri()

IMG = {
 'm_驚き': 'mirai/transparent/mirai_06_surprise.png', 'm_困り': 'mirai/transparent/mirai_07_troubled.png',
 'm_ドヤ': 'mirai/transparent/mirai_08_smug.png', 'm_疑問': 'mirai/transparent/mirai_09_question.png',
 'm_怒り': 'mirai/transparent/mirai_13_rage.png', 'm_落胆': 'mirai/transparent/mirai_15_sigh.png',
 'm_励まし': 'mirai/transparent/mirai_14_cheer.png', 'm_笑顔': 'mirai/transparent/mirai_03_smile.png',
 'h_衝撃': 'hinata/transparent/hinata_11_shock.png', 'h_驚き': 'hinata/transparent/hinata_06_surprise.png',
 'h_困り': 'hinata/transparent/hinata_07_troubled.png', 'h_疑問': 'hinata/transparent/hinata_09_question.png',
 'h_ムッ': 'hinata/transparent/hinata_12_pout.png', 'h_笑顔': 'hinata/transparent/hinata_05_smile.png',
 'h_怒り': 'hinata/transparent/hinata_13_angry.png', 'h_ドヤ': 'hinata/transparent/hinata_08_smug.png',
}

# ---- 漫符（記号）：顔の位置を基準に重ねる ----
def fx(kind, x, y, s=1.0):
    t = f'position:absolute;left:{x}px;top:{y}px;transform:scale({s});transform-origin:0 0;'
    if kind == '汗':
        return f'''<svg style="{t}" width="90" height="130" viewBox="0 0 90 130"><g stroke="#123" stroke-width="5" fill="#8fd8ff">
<path d="M30 10 C 50 45, 62 62, 55 82 A 26 26 0 1 1 8 70 C 10 55, 22 40, 30 10Z"/>
<path d="M70 70 C 80 88, 86 98, 82 108 A 12 12 0 1 1 60 104 C 61 95, 65 86, 70 70Z"/></g>
<path d="M22 64 Q 20 78 30 86" stroke="#fff" stroke-width="6" fill="none" stroke-linecap="round"/></svg>'''
    if kind == '怒り':
        return f'''<svg style="{t}" width="110" height="110" viewBox="0 0 110 110"><g fill="none" stroke-linecap="round">
<g stroke="#fff" stroke-width="22"><path d="M15 40 Q 40 42 42 15"/><path d="M68 15 Q 70 40 95 42"/><path d="M95 68 Q 70 70 68 95"/><path d="M42 95 Q 40 70 15 68"/></g>
<g stroke="#e8203a" stroke-width="11"><path d="M15 40 Q 40 42 42 15"/><path d="M68 15 Q 70 40 95 42"/><path d="M95 68 Q 70 70 68 95"/><path d="M42 95 Q 40 70 15 68"/></g></g></svg>'''
    if kind == '青ざめ':  # 顔の上半分に縦線
        lines = ''.join(f'<rect x="{8+i*22}" y="0" width="7" height="{70+(i%2)*25}" rx="3"/>' for i in range(8))
        return f'<svg style="{t}opacity:.85" width="180" height="100"><g fill="#3a4f9a">{lines}</g></svg>'
    if kind == 'キラキラ':
        star = lambda cx, cy, r, c: f'<path transform="translate({cx} {cy})" d="M0 {-r} Q {r*.18} {-r*.18} {r} 0 Q {r*.18} {r*.18} 0 {r} Q {-r*.18} {r*.18} {-r} 0 Q {-r*.18} {-r*.18} 0 {-r}Z" fill="{c}" stroke="#fff" stroke-width="4"/>'
        return f'<svg style="{t}" width="200" height="200">{star(60,60,52,"#ffd21f")}{star(150,40,28,"#fff36a")}{star(150,140,34,"#ffd21f")}</svg>'
    if kind == '！？':
        return f'<div style="{t}font:900 150px/1 \'Noto Sans CJK JP\';color:#ffe14a;-webkit-text-stroke:14px #111;paint-order:stroke fill;transform:scale({s}) rotate(12deg)">!?</div>'
    if kind == '？？':
        return f'<div style="{t}font:900 120px/1 \'Noto Sans CJK JP\';color:#7fd3ff;-webkit-text-stroke:12px #123;paint-order:stroke fill;transform:scale({s}) rotate(-10deg)">??</div>'
    if kind == 'ガーン':
        return f'<div style="{t}font:900 96px/1 \'Noto Sans CJK JP\';color:#fff;-webkit-text-stroke:14px #2b1a6b;paint-order:stroke fill;transform:scale({s}) rotate(-8deg);letter-spacing:-.05em">ガーン</div>'
    raise KeyError(kind)

def speed_lines(cx, cy, color='#fff', n=56, op=.9):
    import math, random
    random.seed(3)
    ps = []
    for i in range(n):
        a = i / n * 2 * math.pi + random.uniform(-.03, .03)
        r1 = random.uniform(330, 430); w = random.uniform(.010, .025)
        p = lambda r, aa: f'{cx+r*math.cos(aa):.0f},{cy+r*math.sin(aa):.0f}'
        ps.append(f'<polygon points="{p(r1,a)} {p(1600,a-w)} {p(1600,a+w)}"/>')
    return f'<svg style="position:absolute;inset:0;opacity:{op}" width="1280" height="720"><g fill="{color}">{"".join(ps)}</g></svg>'

def char(key, left, top, height, outline='#fff', flip=False, extra=''):
    p = CH / IMG[key]
    w, h = Image.open(p).size
    width = height * w / h
    f = 'transform:scaleX(-1);' if flip else ''
    sh = ' '.join(f'drop-shadow({dx}px {dy}px 0 {outline})' for dx, dy in [(5,0),(-5,0),(0,5),(0,-5)])
    html = (f'<img src="{p.as_uri()}" style="position:absolute;left:{left}px;top:{top}px;height:{height}px;{f}'
            f'filter:{sh} drop-shadow(0 12px 18px rgba(0,0,0,.45));{extra}">')
    # 顔のおおよその位置（立ち絵の上 4〜38%、横 25〜68%）
    face = dict(x1=left + width*.25, x2=left + width*.68, y1=top + height*.04, y2=top + height*.38)
    return html, face

BASE = f'''<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:Maru;src:url({FONT})}}
*{{margin:0;padding:0;box-sizing:border-box}}html,body{{width:1280px;height:720px;overflow:hidden}}
body{{position:relative;font-family:"Noto Sans CJK JP";font-weight:900}}
.st{{paint-order:stroke fill}}
.ch{{position:absolute;right:0;bottom:0}}
</style><body>'''

def page(body):
    return BASE + body + '</body>'

designs = {}

# 1) ピンク〜紫の帯（PIVOT風）
h1, f1 = char('h_衝撃', 820, 150, 640)
m1, g1 = char('m_困り', 980, 40, 620)
designs['01_pink_band'] = page(f'''
<div style="position:absolute;inset:0;background:#fff"></div>
<div style="position:absolute;inset:0;background:radial-gradient(circle at 85% 30%,#ffe3f1 0,#fff 55%)"></div>
<div style="position:absolute;left:0;top:0;width:1280px;height:16px;background:linear-gradient(90deg,#ff3d8b,#7b3dff)"></div>
<div style="position:absolute;left:40px;top:44px;font-size:54px;color:#2a1b4a">AIに賭けた</div>
<div style="position:absolute;left:24px;top:128px;width:800px;padding:18px 24px 26px;background:linear-gradient(100deg,#ff2e7e,#8a3dff);transform:skew(-6deg);border-radius:8px;box-shadow:0 10px 0 #2a1b4a">
 <div style="transform:skew(6deg);font-size:150px;line-height:1;color:#fff;letter-spacing:-.06em;white-space:nowrap">7680<span style="font-size:.6em">億円</span></div></div>
<div style="position:absolute;left:24px;top:342px;width:760px;padding:16px 24px 24px;background:linear-gradient(100deg,#ff2e7e,#8a3dff);transform:skew(-6deg);border-radius:8px;box-shadow:0 10px 0 #2a1b4a">
 <div style="transform:skew(6deg);font-size:136px;line-height:1;color:#fff;letter-spacing:-.04em;white-space:nowrap">の<span style="color:#ffe14a">赤字</span>!?</div></div>
<div style="position:absolute;left:40px;top:590px;font-size:50px;color:#2a1b4a">原因は… <span style="background:#ffe14a;padding:0 12px">電気</span></div>
{m1}{h1}
{fx('青ざめ', f1['x1']+10, f1['y1']-2, .9)}
{fx('汗', g1['x1']-60, g1['y1']+20, .9)}
{fx('ガーン', 860, 640, .9)}
''')

# 2) 数字ドーン（黄色地）
m2, g2 = char('m_ドヤ', 870, 60, 700)
h2, f2 = char('h_驚き', 10, 360, 420, flip=True)
designs['02_big_number'] = page(f'''
<div style="position:absolute;inset:0;background:#ffd400"></div>
<div style="position:absolute;inset:0;background:repeating-conic-gradient(from 0deg at 68% 40%,rgba(255,255,255,.35) 0 6deg,transparent 6deg 18deg)"></div>
<div style="position:absolute;left:300px;top:24px;font-size:66px;color:#111">マイクロンの売上</div>
<div class=st style="position:absolute;left:250px;top:90px;font-size:330px;line-height:1;color:#e5322d;letter-spacing:-.07em;-webkit-text-stroke:26px #fff;filter:drop-shadow(0 12px 0 #111)">4.8<span style="font-size:.55em">倍</span></div>
<div style="position:absolute;left:300px;top:490px;background:#111;color:#fff;font-size:56px;padding:10px 28px 16px;border-radius:12px;transform:rotate(-2deg)">AIがメモリー<span style="color:#ffd400">爆買い</span></div>
<div style="position:absolute;left:310px;top:620px;font:900 38px Maru;color:#111">パソコンが高くなる理由も</div>
{h2}{m2}
{fx('キラキラ', g2['x2']-10, g2['y1']-30, .8)}
{fx('！？', f2['x2']-20, f2['y1']-90, .7)}''')

# 3) 速報（赤×黒×黄）
m3, g3 = char('m_驚き', 860, 70, 680)
h3, f3 = char('h_衝撃', 650, 250, 520)
designs['03_breaking'] = page(f'''
<div style="position:absolute;inset:0;background:radial-gradient(circle at 75% 40%,#d0101e,#5a0008 75%)"></div>
{speed_lines(980, 260, '#ff6a6a', 64, .55)}
<div style="position:absolute;left:0;top:0;width:1280px;height:64px;background:repeating-linear-gradient(-45deg,#ffd400 0 34px,#111 34px 68px)"></div>
<div style="position:absolute;left:30px;top:92px;background:#ffd400;color:#111;font-size:58px;padding:6px 22px 12px;transform:skew(-8deg)">速報 選挙のあと</div>
<div class=st style="position:absolute;left:24px;top:190px;font-size:128px;line-height:1.08;color:#fff;-webkit-text-stroke:18px #111;letter-spacing:-.05em">売上<span style="color:#ffe14a">2倍</span>でも<br>株が<span style="color:#ffe14a;font-size:1.25em">急落</span>!?</div>
<div style="position:absolute;left:30px;top:600px;font-size:54px;color:#fff;border-bottom:8px solid #ffd400">エヌビディアに何が？</div>
{m3}{h3}
{fx('汗', g3['x1']-70, g3['y1']+10, 1)}
{fx('青ざめ', f3['x1']+5, f3['y1'], .75)}''')

# 4) VS 対決（斜めに2分割）
m4, g4 = char('m_ドヤ', 40, 140, 600)
h4, f4 = char('h_怒り', 900, 150, 590)
designs['04_versus'] = page(f'''
<div style="position:absolute;inset:0;background:#1e5bff"></div>
<div style="position:absolute;inset:0;background:#ff3d3d;clip-path:polygon(58% 0,100% 0,100% 100%,42% 100%)"></div>
<div style="position:absolute;inset:0;background:repeating-linear-gradient(90deg,rgba(255,255,255,.07) 0 4px,transparent 4px 28px)"></div>
{m4}{h4}
<div class=st style="position:absolute;left:520px;top:220px;font:italic 900 230px/1 'Noto Sans CJK JP';color:#ffe14a;-webkit-text-stroke:22px #111;filter:drop-shadow(0 10px 0 #111)">VS</div>
<div style="position:absolute;left:0;top:24px;width:1280px;text-align:center"><span style="background:#111;color:#fff;font-size:70px;padding:6px 30px 14px;border-radius:10px">メモリー戦争</span></div>
<div class=st style="position:absolute;left:330px;top:500px;font-size:84px;color:#fff;-webkit-text-stroke:14px #0b2a8a;transform:rotate(-4deg)">マイクロン</div>
<div class=st style="position:absolute;left:690px;top:560px;font-size:84px;color:#fff;-webkit-text-stroke:14px #8a0b0b;transform:rotate(3deg)">サムスン</div>
{fx('怒り', f4['x2']-40, f4['y1']-20, .9)}
{fx('キラキラ', g4['x2']-40, g4['y1']-40, .6)}''')

# 5) 手書きノート（クリーム色の紙）
h5, f5 = char('h_疑問', 860, 120, 620)
m5, g5 = char('m_疑問', 1040, 70, 520)
designs['05_notebook'] = page(f'''
<div style="position:absolute;inset:0;background:#fbf4e2"></div>
<div style="position:absolute;inset:0;background:repeating-linear-gradient(0deg,transparent 0 58px,#cfe0f0 58px 61px)"></div>
<div style="position:absolute;left:96px;top:0;width:4px;height:720px;background:#f2a5a5"></div>
<div style="position:absolute;left:140px;top:40px;font:900 56px Maru;color:#3a3a3a;transform:rotate(-2deg)">ひなたの疑問</div>
<div style="position:absolute;left:130px;top:130px;font:900 120px/1.15 Maru;color:#222;transform:rotate(-2deg)">電気代が<br>高いのは<br><span style="position:relative;color:#e5322d">AIのせい<svg style="position:absolute;left:-24px;top:2px" width="540" height="160"><ellipse cx="270" cy="80" rx="258" ry="70" fill="none" stroke="#e5322d" stroke-width="8" transform="rotate(-3 270 80)"/></svg></span>!?</div>
<div style="position:absolute;left:150px;top:590px;font:900 48px Maru;color:#fff;background:#2c7a4b;padding:8px 22px 12px;border-radius:40px">ソフトバンクGが7680億円の赤字</div>
{m5}{h5}
{fx('？？', f5['x1']-110, f5['y1']-40, .9)}''')

# 6) ひなたの顔アップ＋吹き出し
h6, f6 = char('h_衝撃', 560, -40, 1300)
designs['06_closeup'] = page(f'''
<div style="position:absolute;inset:0;background:#14163a"></div>
{speed_lines(900, 260, '#ffffff', 72, .9)}
{h6}
{fx('汗', f6['x1']-140, f6['y1']+80, 1.3)}
<div style="position:absolute;left:30px;top:40px;width:600px;height:330px;background:#fff;border:8px solid #111;border-radius:50%;"></div>
<svg style="position:absolute;left:470px;top:250px" width="200" height="140"><path d="M10 30 L190 120 L60 10Z" fill="#fff" stroke="#111" stroke-width="8" stroke-linejoin="round"/><path d="M14 20 L60 14 L100 60Z" fill="#fff"/></svg>
<div style="position:absolute;left:30px;top:90px;width:600px;text-align:center;font-size:100px;line-height:1.1;color:#111">パソコンが<br><span style="color:#e5322d">高すぎ</span>!!</div>
<div class=st style="position:absolute;left:30px;top:420px;font-size:110px;line-height:1.1;color:#ffe14a;-webkit-text-stroke:18px #111">犯人は<br>メモリー!?</div>''')

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width': 1280, 'height': 720})
        for name, html in designs.items():
            f = OUT / f'{name}.html'; f.write_text(html, encoding='utf-8')
            await pg.goto(f.as_uri()); await pg.wait_for_timeout(300)
            await pg.screenshot(path=str(OUT / f'{name}.png'))
        await b.close()
asyncio.run(main())
print('ok')
