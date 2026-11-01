# video anime

Skill cho Claude Code: biến giọng đọc và kịch bản thành video hoạt hình giải thích kiểu chibi, dựng sẵn thành timeline nhiều lớp trong DaVinci Resolve.

Nhân vật, bối cảnh và đạo cụ đều vẽ bằng code, không cần công cụ tạo ảnh AI. Khẩu hình tự chạy theo giọng đọc. Ảnh thật lấy từ Wikimedia Commons kèm thông tin giấy phép.

## Cài đặt

Cần Python 3.10+, ffmpeg và DaVinci Resolve. Mới thử trên Resolve Studio 21.1.1, Windows 10.

```bash
git clone https://github.com/tinhkiemcn1-spec/video-anime.git
```

```bash
cd video-anime
```

```bash
python install.py
```

Lệnh này cài thư viện, tạo hiệu ứng âm thanh, chép skill vào `~/.claude/skills/video-anime` và thêm mục **video anime Import** vào menu Workspace > Scripts của Resolve.

Resolve Studio: bật Preferences > System > General > External scripting = Local để Claude tự nhập timeline. Resolve Free: nhập bằng menu Workspace > Scripts (đường này chưa được thử trên bản Free); `--check` cần Studio.

## Sử dụng

Trong Claude Code:

```text
/video-anime Làm video từ giọng đọc E:\du-an\vo.mp3, kịch bản E:\du-an\kich-ban.docx
```

Claude chép lời, tìm ảnh, lập `plan.json`, render các lớp rồi dựng timeline:

| Track | Nội dung |
|---|---|
| V1 | Nền, ảnh thật, TV |
| V2 | Nhân vật có khẩu hình (ProRes 4444 trong suốt) |
| V3 | Chữ, bong bóng, dấu |
| V4 | Clip meme do bạn cung cấp |
| A1, A2, A3 | Giọng đọc, hiệu ứng, nhạc |

## Giới hạn

- Giọng đọc phải là file bạn cung cấp; skill không tự tạo giọng.
- Nhạc nền và clip meme do bạn đưa vào.
- Nhân vật là rối vẽ bằng code: nét gọn hơn tranh vẽ tay, tay chân không có chu kỳ đi bộ. Bối cảnh mới phải viết thêm hàm vẽ.

## Nhân vật trụ

`host_preset: "mau"` theo cách dựng hình của video mẫu. Nếu nhân vật đó không phải của kênh bạn, dùng `"goc"` hoặc thêm bộ màu riêng trong `scripts/va_host.py` trước khi đăng video.

## Tài liệu

- [SKILL.md](SKILL.md): quy trình Claude làm theo
- [references/phan-tich-video.md](references/phan-tich-video.md): phân tích phong cách
- [references/plan-format.md](references/plan-format.md): định dạng `plan.json`

## Giấy phép

Mã nguồn: MIT. Font trong `assets/fonts` (Patrick Hand, Pangolin, Itim): SIL OFL 1.1, xem `assets/fonts/OFL.txt`. Tham khảo cách làm việc với Resolve từ [Thang-Edit](https://github.com/tinhkiemcn1-spec/Thang-Edit).
