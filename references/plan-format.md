# plan.json

File chính của mỗi video, nằm tại `<edit>/plan.json`. Xem ví dụ đầy đủ: `examples/demo_plan.json`.

```json
{
 "title": "Tên video",
 "vo": "vo.wav",
 "host_preset": "mau",
 "music": "nhac.wav",
 "music_db": -24,
 "sfx_db": -8,
 "cast": { "linh": {"hat":"helmet","robe":"#6a2a22"} },
 "shots": [ ... ]
}
```

Các shot phải liền nhau: `t` của shot sau bằng `end` của shot trước, shot đầu từ 0, shot cuối hết VO.

## Trường chung của shot

| Trường | Ý nghĩa |
|---|---|
| `t`, `end` | Giây trên VO |
| `type` | `host` `photo` `card` `scene` `tv` `map` `list` `stack` |
| `bg` | `white parchment mountains field forest desert room office throne palace hut tents river castle dungeon` |
| `seed` | Đổi để có bản khác của cùng bối cảnh; giữ nguyên để lặp lại đúng nơi đó |
| `mood` | `day`, `night`, `gray` (hồi tưởng đen trắng) |
| `title`, `title_y`, `title_size` | Tiêu đề trên đầu khung; trên `parchment` tự thành chữ đỏ |
| `sub`, `sub_x`, `sub_y` | Dòng chữ phụ |
| `labels` | `[{"text","x","y","size","style"}]`; `style` là `sticker` (trắng viền đen) hoặc `plain` |
| `bubble` | `{"kind":"speech|think|shout","text"|"char"|"image","x","y","w","h","tail":[-1,1]}` |
| `marks` | `[{"kind":"x|anger|sweat|laugh|!!!|???","x","y","s"}]` |
| `sfx` | `"pop"` hoặc `["whoosh@2.2","ding"]`, số sau `@` là giây tính từ đầu shot. Có: `pop whoosh ding boing thud tick fail` |
| `meme` | `{"file","opacity":0.55,"start":0}`: clip phủ V4. Chỉ hiện trong Resolve, không có trong preview |

## Từng loại shot

- `host`: nhân vật trụ một mình.
- `photo`: `"photo":"photos/x_1.jpg"`, ảnh trái, người dẫn phải.
- `map`: `"photo"` phủ kín khung, `"rings":[{"x","y","r"}]`.
- `card`: thẻ giới thiệu: `title` + một nhân vật trong `cast`.
- `scene`: bối cảnh + `cast`, có thể thêm `host`.
- `tv`: bàn + màn hình tự chiếu cảnh `scene` gần nhất, nhân vật trụ cận cảnh bên phải.
- `list`: `"items":[{"text":"Trận X\n(1788)","char":"linh"|"image":"..."}]`, camera lia giữa các huy hiệu.
- `stack`: `"items":[{"title","char"|"image"}]`, tiêu đề đẩy dọc có nhòe.

## host

`{"pose","eyes","brow","mouth","close","x","y","scale","flip","talk"}`

- pose: `idle thumb point_up present point shrug ok think read hip`
- eyes: `line closed wide happy shut`
- brow: `none up angry worried`
- mouth (khi không nói): `closed small open wide smile smirk frown laugh`
- `close: true`: khung cận. `talk` mặc định true với host.

## cast (khai báo)

`{"skin","hair","hair_col","hat","hat_col","beard","beard_col","robe","sash","cape","flag"}`

- skin: `light tan brown dark pale blue`
- hair: `none short side long bob bun bald spiky curly princess`
- hat: `none crown turban helmet officer conical wizard tophat cap headwrap royal_cap`
- beard: `none mustache goatee full long`
- flag: `{"bands":["#e00","#fff","#e00"],"dir":"h"}` biến đầu thành cờ

## cast (trong shot)

`{"id","x","y","scale","pose","expr","mouth","flip","talk","move":[x0,x1],"loop":2,"crowd":[cols,rows],"dx","dy"}`

- pose: `idle point fist pray raised think cross sword scroll hand_chin`
- expr: `normal angry sad smug shock happy sleep cry`
- `y` là tọa độ chân; `scale` 1.0 ≈ cao 600 px, cảnh đối thoại cận dùng 1.0–1.2 với y 1100–1160 để cắt ở ngực như mẫu.
- `move` trượt ngang, `loop` số lần chạy lại trong shot.
- `crowd` tạo đám đông nhân bản, nằm ở lớp nền.
- Chỉ đặt `talk: true` cho người đang nói.
