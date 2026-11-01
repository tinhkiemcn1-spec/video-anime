---
name: video-anime
description: Làm trọn video hoạt hình giải thích kiểu chibi (nhân vật trụ dạng que dẫn chuyện, dàn nhân vật đầu to, bối cảnh vẽ, ảnh thật minh họa, giọng kể hài) rồi dựng thành timeline nhiều lớp trong DaVinci Resolve. Dùng khi người dùng gõ /video-anime, "video anime", hoặc muốn làm video kiểu "những cuộc chiến ngớ ngẩn nhất", "truyện cổ tích lmao", "top nhân vật lịch sử", hoạt hình kể chuyện/lịch sử từ giọng đọc và kịch bản, tạo nhân vật hay bối cảnh hoạt hình theo phong cách đó.
---

# video anime

Từ giọng đọc + kịch bản ra timeline DaVinci Resolve: nền, nhân vật có khẩu hình, chữ, ảnh thật, hiệu ứng âm thanh. Mọi hình đều vẽ bằng code nên không cần công cụ tạo ảnh AI.

Trước khi lên kế hoạch, đọc `references/phan-tich-video.md` (phong cách) và `references/plan-format.md` (định dạng).

## Quy tắc cứng

1. **VO giữ nguyên**: không cắt, không kéo. Timeline dài đúng bằng VO.
2. **Không ghi đè timeline có sẵn.** Mỗi lần dựng một tên mới.
3. **Không bịa sự kiện.** Tên, năm, địa danh trong kịch bản và trên màn hình phải có nguồn; không chắc thì báo người dùng.
4. **Ảnh thật lấy từ `fetch_photos.py`** (Wikimedia Commons, có giấy phép), hoặc ảnh người dùng đưa. Nhìn sheet trước khi dùng. Giữ `photos/credits.csv` để đưa vào mô tả video.
5. **Meme chỉ dùng clip người dùng cung cấp.** Không tự tải clip có bản quyền.
6. **Nhịp theo mẫu**: trung vị 5–6 s một cảnh, 7–8 cảnh/phút. Cắt thẳng; không thêm zoom, particle hay chuyển cảnh trang trí mà mẫu không có.

## Quy trình

Script ở `scripts/` của skill, chạy `python -X utf8`. Thư mục dựng `<edit>` do người dùng chọn. Chưa có `assets/sfx/*.wav` thì chạy `make_sfx.py`.

1. **Đầu vào.** Cần file VO. Chỉ có chủ đề thì soạn kịch bản theo cấu trúc trong phần phân tích, đưa người dùng duyệt và thu giọng. Không có VO thì dừng ở kịch bản, nói rõ phần còn thiếu.
2. **Chép lời**: `transcribe.py <vo> <edit> --prompt "<tên riêng>"` tạo `transcript.json` gồm câu có thời gian. Lời trong VO là chuẩn, kịch bản dùng để sửa chính tả tên.
3. **Ảnh thật**: `fetch_photos.py <edit> "<từ khóa>" --name <id>` cho từng nhân vật, địa danh, bản đồ. Xem `<id>_sheet.jpg`, chọn ảnh đúng người đúng nơi.
4. **Lập kế hoạch** `plan.json`: khai báo `cast` trước, sau đó chia shot theo câu trong transcript.
   - Mục mới: `card` hoặc `stack`, kèm `sfx` nhẹ.
   - Nói về người, nơi có thật: `photo`, `map`.
   - Tường thuật: `scene`, nhân vật nói đặt `talk: true`.
   - Bình luận, đùa: `host` hoặc `tv`, khung cận cho phản ứng.
   - Giữ một nơi một `bg` + `seed`. Dùng `gray` cho hồi tưởng.
   - SFX ít: mỗi cái gắn với một thứ nhìn thấy trên hình.
5. **Kiểm tra**: `check_plan.py <edit>`, sửa tới khi ra `PLAN OK`.
6. **Render**: `render_shots.py <edit>` tạo `layers/`, `manifest.json`, `preview.mp4`. Xem preview bằng sheet khung hình, đối chiếu từng shot với lời. Sửa shot lẻ: `--only 3,7`, rồi xuất lại preview bằng lần chạy đầy đủ.
7. **Dựng**: mở Resolve và project đích, `resolve_build.py <edit> --name "<tên>" --push --check`.
   - Studio: tự nhập và tự render so sánh, xem `resolve/check_sheet.jpg`.
   - Free (chưa thử thực tế): bỏ `--push --check`, trong Resolve chọn Workspace > Scripts > video anime Import.
8. **Báo cáo**: tên timeline, số shot, phần chưa làm, shot chưa có tư liệu đúng, nguồn ảnh.

## Timeline tạo ra

V1 nền, V2 nhân vật (ProRes 4444 alpha), V3 chữ và dấu, V4 meme. A1 VO, A2 SFX, A3 nhạc. Bạn sửa được từng lớp trong Resolve. Tổng dung lượng khoảng 3 MB mỗi giây video.

## Tùy biến

- Nhân vật trụ: `host_preset` là `mau` hoặc `goc`; thêm bộ màu trong `va_host.PRESETS`.
- Nhân vật, bối cảnh mới: thêm hàm trong `va_cast.py`, `va_bg.py`; thêm vào `NAMES`, `HATS`, `HAIRS` để `check_plan.py` nhận.
- Mẫu mới: `analyze_ref.py <video> <out>` đo nhịp cắt, âm lượng, tạo contact sheet.

## Lỗi đã gặp

- Card NVIDIA báo có CUDA nhưng thiếu `cublas64_12.dll`: chỉ lỗi ở bước encode đầu tiên, nên `transcribe.py` bọc cả quá trình rồi chuyển sang CPU.
- PyAV mới làm hỏng bộ đọc âm thanh của faster-whisper: audio luôn đi qua ffmpeg.
- Resolve đánh số audio từ lane thấp nhất: VO lane −3 mới là A1.
- Resolve nhận PNG làm clip trong spine FCPXML bình thường, ảnh tĩnh không giới hạn 5 s như qua `AppendToTimeline`.
- Không dùng VP9 hay `.webm` cho Resolve; alpha luôn là ProRes 4444.
- Windows console: chạy `python -X utf8` cho tên tiếng Việt.
