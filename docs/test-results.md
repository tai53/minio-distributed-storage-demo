# Kết quả kiểm thử

## 1. Upload / Download

| Loại file | Kích thước | Thời gian upload | Thời gian download | Kết quả |
|---|---|---|---|---|
| .txt | 56 bytes | < 1s | < 1s | ✅ Thành công |
| .jpg | | | | |
| .mp4 | | | | |

*(Ghi chú: bảng này do Người 2 phụ trách điền đầy đủ với file ảnh/video/file lớn — dòng .txt là số liệu tham khảo từ quá trình test failover.)*

## 2. Test Fault Tolerance (tắt node)

| Kịch bản | Số node còn lại | Kết quả | Ghi chú |
|---|---|---|---|
| Tắt 1 node (minio2) | 3/4 | ✅ Thành công | Upload/download bình thường ngay lập tức, không có độ trễ đáng kể |
| Tắt 2 node (minio2 + minio3) | 2/4 | ⚠️ Đọc OK, Ghi thất bại | `bucket_exists` (thao tác đọc) chạy thành công, nhưng `upload` (thao tác ghi) bị treo và timeout — không đủ write quorum. MinIO yêu cầu tối thiểu 3/4 node hoạt động để đảm bảo ghi dữ liệu an toàn |
| Khôi phục 2 node, test ngay lập tức | 4/4 (đang healing) | ⚠️ Lỗi tạm thời (NoSuchKey) | Upload thành công nhưng download báo lỗi "NoSuchKey" — do cluster đang trong quá trình đồng bộ lại dữ liệu (healing) giữa các node, Nginx định tuyến request đọc sang node chưa kịp nhận bản sao |
| Khôi phục 2 node, đợi ~20 giây rồi test | 4/4 (đã ổn định) | ✅ Thành công | Hệ thống hoạt động bình thường trở lại sau khi cluster hoàn tất healing |

## 3. Nhận xét

Kết quả kiểm thử cho thấy khả năng chịu lỗi của MinIO distributed mode (4 node, erasure coding) có giới hạn rõ ràng và khác nhau giữa thao tác đọc và ghi:

- **Khả năng đọc (read)**: hệ thống chịu được mất tối đa 2/4 node — vẫn đọc được dữ liệu nhờ cơ chế erasure coding tái tạo từ các shard còn lại.
- **Khả năng ghi (write)**: yêu cầu khắt khe hơn — cần tối thiểu 3/4 node hoạt động (write quorum) để đảm bảo đủ bản sao/parity trước khi xác nhận ghi thành công. Khi chỉ còn 2/4 node, thao tác ghi bị từ chối/treo để bảo toàn tính nhất quán dữ liệu, không cho phép ghi dữ liệu "nửa vời".
- **Thời gian healing sau khi phục hồi node**: đây là phát hiện quan trọng ít được nhắc tới trong tài liệu — dù Docker báo container đã ở trạng thái "healthy" ngay sau khi khởi động lại, cụm MinIO vẫn cần thêm khoảng 15-20 giây để đồng bộ lại dữ liệu nội bộ giữa các node. Nếu test ngay trong khoảng thời gian này, có thể gặp lỗi đọc dữ liệu tạm thời (NoSuchKey) dù trước đó ghi đã thành công. Đây không phải lỗi cấu hình mà là hành vi bình thường của hệ thống phân tán trong giai đoạn tự phục hồi (self-healing).

Kết luận: hệ thống đạt được mục tiêu chịu lỗi cơ bản của kiến trúc distributed storage, nhưng có đánh đổi rõ ràng giữa tính sẵn sàng (availability) và tính nhất quán (consistency) — đúng theo nguyên lý CAP quen thuộc trong hệ thống phân tán.