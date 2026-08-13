#!/bin/bash
# Script test khả năng chịu lỗi (fault tolerance) của MinIO distributed mode.
# Tắt 1 node, kiểm tra dữ liệu vẫn upload/download được, sau đó bật lại node.
#
# Chạy: bash scripts/failover_test.sh

NODE_TO_STOP="minio2"

echo "===== BƯỚC 1: Trạng thái container trước khi test ====="
docker compose ps

echo ""
echo "===== BƯỚC 2: Tắt node $NODE_TO_STOP để mô phỏng sự cố ====="
docker compose stop "$NODE_TO_STOP"

echo ""
echo "===== BƯỚC 3: Kiểm tra hệ thống vẫn hoạt động (upload/download) ====="
python3 scripts/upload_download.py

echo ""
echo "===== BƯỚC 4: Khởi động lại node $NODE_TO_STOP ====="
docker compose start "$NODE_TO_STOP"

echo ""
echo "===== BƯỚC 5: Trạng thái container sau khi khôi phục ====="
docker compose ps

echo ""
echo "Hoàn tất test failover. Ghi lại kết quả vào docs/test-results.md"
