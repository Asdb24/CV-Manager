# Hồ sơ tuyển dụng

Nền tảng quản lý CV của một đơn vị tuyển dụng: khung Windows Tauri, website công khai Next.js, API/worker và cấu hình có kiểm tra. Phases 01–05 đã PASS trong phạm vi đã kiểm chứng. Roadmap 45 phase và quality CI trên GitHub đã có bằng chứng; Phase 06 là bước tiếp theo khi có prompt riêng. Giao diện hiện chưa hỗ trợ đăng nhập, hồ sơ, điểm đánh giá hoặc nộp CV. Các chức năng này được thực hiện ở đúng phase sở hữu.

Đọc [trạng thái hiện tại](docs/STATUS.md), [kiến trúc](docs/architecture/ARCHITECTURE.md), [cấu hình](docs/architecture/CONFIGURATION.md), [luồng dữ liệu](docs/architecture/DATA_FLOW.md) và [cách tái lập kiểm tra](docs/architecture/REPRODUCIBILITY.md), [roadmap 45 phase](docs/architecture/PHASE_ROADMAP.md) và [quality CI](docs/ci/QUALITY_WORKFLOW.md). Đây là môi trường phát triển dùng dữ liệu tổng hợp; chưa phải bộ cài phát hành.

Các lệnh chuẩn gồm `npm run install:frozen`, `npm run client:check` và `npm run test`. Bản dựng bắt buộc chọn tệp cấu hình và profile rõ ràng. Xem tài liệu tái lập trước khi chạy.

Kiểm tra database synthetic Phase 03 trên môi trường phát triển đã có PostgreSQL 18.6 và dependencies đã khóa:

```powershell
node scripts/tasks.mjs database:check --config infra/config/database-test.json
npm run migration:check -- --config infra/config/database-test.json
npm run verify:checkpoint -- --database-config infra/config/database-test.json
```

Lệnh database chỉ quản lý cluster có dấu sở hữu của dự án trong `.local/phase03`; thông tin kết nối, giới hạn và khối lượng dữ liệu nằm trong cấu hình được kiểm tra kiểu. Không dùng các fixture này cho CV thật. Đọc [thiết kế database](docs/database/DATABASE_DESIGN.md) và [bằng chứng Phase 03](docs/phases/PHASE_03_VERIFICATION.md). Các lệnh trên dành cho lập trình viên; chưa phải quy trình cài đặt người dùng cuối.
