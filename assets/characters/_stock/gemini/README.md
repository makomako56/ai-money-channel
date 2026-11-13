# Gemini で作った表情のストック（元画像）

合成前の元画像を置く。動画工場は使わない（登録済みの表情は `../mirai/` `../hinata/` と `config/characters.yaml`）。

| ファイル | 中身 | 状態 |
|---|---|---|
| 2026-11-13_mirai_sheet1_kira_jitome.jpg | ミライの表情一覧（真ん中にキラキラ、懐疑・心痛・苛立ちほか） | キラキラ→mirai_22_sparkle、懐疑→mirai_21_jitome に合成済み。心痛・苛立ちは顔が小さく色あせるため未使用 |
| 2026-11-13_mirai_sheet2_scream.jpg | ミライの表情一覧（真ん中に絶叫） | mirai_23_scream に合成済み |
| 2026-11-13_student_pointing_NOT_hinata.jpg | 生徒の「指さし＋叫び」 | **ひなたではない別人**（黒っぽい長い髪・一つ結び・金のリボン）。ひなたに合成できないため保留 |
| 2026-11-13_student_headhold_NOT_hinata.jpg | 生徒の「頭を抱える」 | 同上。保留 |

注意：Gemini の一覧は服（金のリボン・フリル）と肌の色が基本画像と違う。顔だけを基本画像に合成して使う。
| 2026-11-13_hinata_sheet1_mild.jpg | ひなたの表情一覧（驚き・ニヒル・照れ・羞恥・決意） | ひなた本人で服も一致。表情は控えめ（サムネ用の大げさな顔ではない）。ニヒル・照れ・決意は今後の合成候補 |
| 2026-11-13_hinata_glare.jpg ほか3枚（scream・sparkle・cry） | ひなたの大きな顔4枚（にらみ・絶叫・キラキラ・号泣） | hinata_21〜24 に合成済み |
| 2026-11-13_hinata_cute_*.jpg（6枚） | ひなたの「かわいい版」大きな顔（ぷんぷん・頭を抱える・指さし・ジト目・号泣・キラキラ） | キラキラ・号泣は hinata_23・24 をこの版で差し替え、ぷんぷん→hinata_25、ジト目→hinata_26。6枚とも背景を抜いた版を assets/characters/hinata/closeup/ に保存（顔アップのサムネ用。characters.yaml には未登録） |
