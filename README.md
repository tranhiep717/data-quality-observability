
# DATA QUALITY & OBSERVABILITY PLATFORM

## 1. Giới thiệu

Data Quality & Observability Platform là hệ thống hỗ trợ
kiểm tra chất lượng và giám sát sự thay đổi của dữ liệu.

Hệ thống cho phép người dùng đọc dữ liệu từ CSV hoặc MySQL,
phân tích dữ liệu, thiết lập quy tắc kiểm tra, tính điểm
chất lượng và theo dõi sự thay đổi giữa các lần chạy.

Ứng dụng được xây dựng bằng Python, Pandas, Streamlit,
MySQL và Plotly.

## 2. Công nghệ sử dụng

| Công nghệ | Vai trò |
|---|---|
| Python | Xử lý nghiệp vụ |
| Pandas | Đọc và phân tích dữ liệu |
| MySQL | Lưu cấu hình và kết quả kiểm tra |
| Streamlit | Xây dựng giao diện |
| Plotly | Trực quan hóa biểu đồ |
| MySQL Connector | Kết nối Python với MySQL |

## 3. Chức năng chính

### 3.1. Data Ingestion
- Đọc dữ liệu từ file CSV.
- Đọc bảng từ MySQL.
- Đăng ký nguồn và dataset.
- Tự động đọc lại dữ liệu MySQL trước khi kiểm tra.

### 3.2. Data Profiling
- Thống kê số dòng và số cột.
- Thống kê giá trị NULL.
- Phát hiện dòng trùng lặp.
- Phân tích từng cột dữ liệu.

### 3.3. Data Quality Rules

Hỗ trợ 7 loại quy tắc:

1. NOT_NULL: Kiểm tra dữ liệu không được NULL.
2. UNIQUE: Kiểm tra tính duy nhất.
3. BETWEEN: Kiểm tra giá trị trong khoảng.
4. MIN_VALUE: Kiểm tra giá trị tối thiểu.
5. MAX_VALUE: Kiểm tra giá trị tối đa.
6. ALLOWED_VALUES: Kiểm tra giá trị cho phép.
7. REGEX: Kiểm tra định dạng chuỗi.

### 3.4. Quality Engine
- Áp dụng các quy tắc cho dữ liệu.
- Đếm số dòng không đạt từng quy tắc.
- Tính tỷ lệ đạt của từng quy tắc.
- Tổng hợp thành Quality Score.
- Lưu kết quả kiểm tra vào MySQL.

### 3.5. Data Observability
- Theo dõi số dòng giữa các lần chạy.
- Theo dõi số lượng NULL.
- Theo dõi số lượng dữ liệu trùng lặp.
- Phát hiện thay đổi số cột, tên cột và kiểu dữ liệu.
- So sánh Quality Score giữa các lần chạy.

### 3.6. Alert System

Hệ thống hỗ trợ các cảnh báo:

- LOW_QUALITY
- QUALITY_DROP
- VOLUME_DROP
- NULL_INCREASE
- SCHEMA_DRIFT

Người dùng có thể xem, đánh dấu đã xử lý
hoặc mở lại cảnh báo trên Dashboard.

### 3.7. Dashboard
- Hiển thị điểm chất lượng dữ liệu.
- Hiển thị lịch sử Pipeline Runs.
- Biểu đồ Quality Score.
- Kết quả kiểm tra từng quy tắc.
- Cảnh báo chất lượng dữ liệu.
- Thống kê biến động và Schema Drift.

## 4. Kiến trúc hệ thống

CSV / MySQL Source
        |
        v
Data Ingestion
        |
        v
Data Profiling
        |
        v
Quality Rules
        |
        v
Quality Engine
        |
        v
MySQL Results Storage
        |
        v
Monitoring & Alerts
        |
        v
Streamlit Dashboard

Hệ thống sử dụng MySQL để lưu cấu hình,
lịch sử và kết quả kiểm tra.

Việc kiểm tra được kích hoạt khi người dùng
thực hiện thao tác trên giao diện.

## 5. Cấu trúc dự án

data-quality-observability/
|
|-- app.py
|-- modules/
|   |-- database.py
|   |-- ingestion.py
|   |-- profiling.py
|   |-- rules.py
|   |-- quality.py
|   |-- monitoring.py
|   |-- alerts.py
|
|-- pages/
|   |-- 1_Dashboard.py
|   |-- 2_Data_Quality.py
|   |-- 3_Quality_Rules.py
|   |-- 4_Datasets.py
|   |-- 5_Profiling.py
|   |-- 6_MySQL_Source.py
|
|-- tests/
|-- database_schema.sql
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md

## 6. Cài đặt

### Bước 1: Cài đặt

Cần có:
- Python
- MySQL Server
- MySQL Workbench (tùy chọn)

### Bước 2: Tạo môi trường ảo

Windows PowerShell:

python -m venv .venv

.\.venv\Scripts\Activate.ps1

### Bước 3: Cài thư viện

python -m pip install -r requirements.txt

### Bước 4: Tạo database

Tạo database có tên:

data_quality_platform

Import cấu trúc từ file database_schema.sql.

Chú ý:
File SQL có lệnh DROP TABLE IF EXISTS.
Chỉ import vào database mới hoặc database thử nghiệm,
không import vào database đang chứa dữ liệu cần giữ.

### Bước 5: Cấu hình kết nối

Sao chép:

.env.example -> .env

Điền các thông tin kết nối MySQL tương ứng
với modules/database.py.

Không đưa mật khẩu thật lên GitHub.

### Bước 6: Chạy ứng dụng

python -m streamlit run app.py

Mở địa chỉ được Streamlit cung cấp,
thường là http://localhost:8501

## 7. Hướng dẫn sử dụng

### CSV
1. Đăng ký dataset CSV.
2. Tải file CSV lên.
3. Phân tích Data Profiling.
4. Tạo Quality Rules.
5. Chạy Quality Check.
6. Xem kết quả trên Dashboard.

### MySQL
1. Mở trang MySQL Source.
2. Chọn database và bảng dữ liệu.
3. Đăng ký dataset nếu chưa có.
4. Đọc dữ liệu và xem Profiling.
5. Tạo Quality Rules.
6. Chạy Quality Check.
7. Xem Monitoring và Alerts trên Dashboard.

## 8. Cơ sở dữ liệu quản lý

Hệ thống sử dụng 7 bảng:

1. data_sources
2. datasets
3. quality_rules
4. pipeline_runs
5. quality_results
6. dataset_metrics
7. alerts

## 9. Kiểm thử

Các trường hợp đã thực hiện trong quá trình phát triển:

- Kiểm thử 7 Quality Rules.
- Kiểm thử dữ liệu có NULL và trùng lặp.
- Kiểm thử VOLUME_DROP.
- Kiểm thử SCHEMA_DRIFT.
- Kiểm thử NULL_INCREASE.
- Kiểm thử bảng MySQL rỗng.
- Kiểm thử quy tắc tham chiếu cột không tồn tại.
- Giả lập lỗi kết nối MySQL.
- Kiểm tra cơ chế hạn chế chạy liên tiếp.

Các lệnh kiểm thử chính:

python -m tests.test_7_rules

python -m tests.test_monitoring_alerts

## 10. Giới hạn và hướng phát triển

- Chưa tự động lập lịch kiểm tra định kỳ.
- Cảnh báo hiện được lưu và hiển thị trên giao diện.
- Chưa tích hợp gửi cảnh báo qua email.
- Có thể mở rộng để kết nối thêm các nguồn dữ liệu khác.
- Có thể triển khai tự động hóa Data Quality Pipeline.

## 11. Kết luận

Dự án xây dựng một hệ thống kiểm tra chất lượng
và giám sát biến động dữ liệu trên nền tảng Python.

Hệ thống giúp phát hiện dữ liệu không hợp lệ,
theo dõi thay đổi qua nhiều lần chạy và hỗ trợ
người dùng quan sát chất lượng dữ liệu trực quan.
