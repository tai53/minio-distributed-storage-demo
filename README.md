# Mô phỏng hệ thống lưu trữ phân tán bằng MinIO

Bài tập lớn môn Điện toán đám mây — Đề tài 7: mô phỏng nguyên lý lưu trữ đối tượng phân tán (distributed object storage) bằng MinIO, tương tự các dịch vụ cloud storage thực tế như Amazon S3.

## Mục tiêu

- Hiểu nguyên lý lưu trữ phân tán và khác biệt so với lưu trữ tập trung truyền thống.
- Triển khai MinIO ở cả chế độ standalone và distributed mode bằng Docker.
- Thử nghiệm khả năng chịu lỗi (fault tolerance) khi một hoặc nhiều node gặp sự cố.
- So sánh object storage với file storage trên các tiêu chí kỹ thuật.

## Kiến trúc hệ thống

```
Client
  │
  ▼
Load Balancer (Nginx)
  │
  ├── MinIO Node 1
  ├── MinIO Node 2
  ├── MinIO Node 3
  └── MinIO Node 4
```

4 node MinIO chạy ở chế độ distributed, sử dụng erasure coding để chia dữ liệu thành các phần (data shard) và phần dự phòng (parity shard), đảm bảo dữ liệu vẫn truy xuất được ngay cả khi một số node ngừng hoạt động.

## Công nghệ sử dụng

| Thành phần | Công cụ |
|---|---|
| Object storage | MinIO |
| Container hóa | Docker, Docker Compose |
| Load balancer | Nginx |
| Client test | Python (thư viện `minio` hoặc `boto3`) |
| Quản lý qua CLI | MinIO Client (`mc`) |

## Cấu trúc thư mục

```
minio-distributed-storage-demo/
├── README.md
├── .gitignore
├── docker-compose.yml          # Cấu hình MinIO distributed mode (4 node)
├── docker-compose.single.yml   # Cấu hình standalone mode (để so sánh)
├── scripts/
│   ├── upload_download.py      # Script test upload/download qua API
│   └── failover_test.sh        # Script tắt node để test fault tolerance
├── docs/
│   ├── architecture.png        # Sơ đồ kiến trúc hệ thống
│   └── test-results.md         # Kết quả đo hiệu năng và fault tolerance
└── .env.example                # Mẫu biến môi trường (không chứa key thật)
```

## Hướng dẫn cài đặt và chạy

### 1. Yêu cầu môi trường

- Docker và Docker Compose đã cài đặt
- Python 3.8+ (nếu chạy script test)

### 2. Cấu hình biến môi trường

Sao chép file mẫu và điền thông tin:

```bash
cp .env.example .env
```

Chỉnh sửa `.env` với access key/secret key riêng của bạn. **Không commit file `.env` lên Git.**

### 3. Khởi chạy MinIO distributed mode

```bash
docker-compose up -d
```

Kiểm tra các container đang chạy:

```bash
docker ps
```

### 4. Truy cập MinIO Console

Mở trình duyệt tại `http://localhost:9001` và đăng nhập bằng access key/secret key đã cấu hình.

### 5. Tạo bucket và test upload/download

Qua giao diện web, hoặc bằng script:

```bash
python scripts/upload_download.py
```

### 6. Test khả năng chịu lỗi (fault tolerance)

```bash
bash scripts/failover_test.sh
```

Script sẽ tắt một node và kiểm tra dữ liệu vẫn truy xuất được bình thường.

## Kết quả kiểm thử

Xem chi tiết bảng số liệu (thời gian upload/download, kết quả khi mất node) tại [`docs/test-results.md`](docs/test-results.md).

## So sánh File Storage và Object Storage

| Tiêu chí | File Storage | Object Storage |
|---|---|---|
| Đơn vị lưu trữ | File trong cây thư mục | Object phẳng, có metadata + ID riêng |
| Khả năng mở rộng | Hạn chế | Gần như vô hạn, mở rộng ngang tốt |
| Cách truy cập | Giao thức file (NFS, SMB) | HTTP API (REST, S3 API) |
| Trường hợp phù hợp | Ứng dụng cần thao tác file thường xuyên | Lưu trữ dữ liệu lớn, ít thay đổi |
| Ví dụ | NFS, Windows File Share | MinIO, Amazon S3, Azure Blob |

## Ghi chú bảo mật

- File `.env` chứa access key/secret key thật **không được commit** lên Git, đã được thêm vào `.gitignore`.
- Nếu vô tình lộ key, cần thu hồi (revoke) và tạo key mới ngay trong MinIO Console.
