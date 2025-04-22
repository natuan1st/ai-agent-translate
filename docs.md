# Hướng dẫn sử dụng API Dịch thuật (Translation API)

Tài liệu này hướng dẫn cách cài đặt, cấu hình và sử dụng API dịch thuật được triển khai trong file `main.py`.

## Mục lục

- [Tổng quan](#tổng-quan)
- [Cài đặt](#cài-đặt)
- [Cấu hình](#cấu-hình)
- [Chạy API](#chạy-api)
- [Sử dụng API](#sử-dụng-api)
- [Các tham số và mô hình dữ liệu](#các-tham-số-và-mô-hình-dữ-liệu)
- [Xử lý lỗi](#xử-lý-lỗi)
- [Ví dụ](#ví-dụ)

## Tổng quan

API dịch thuật này được xây dựng bằng FastAPI và LangChain, sử dụng mô hình Gemini của Google để dịch văn bản giữa các ngôn ngữ. API này cung cấp một endpoint đơn giản để gửi yêu cầu dịch và nhận kết quả dịch.

## Cài đặt

### Yêu cầu hệ thống

- Python 3.8 trở lên
- Các thư viện được liệt kê trong `requirements.txt`

### Cài đặt các thư viện

```bash
# Tạo và kích hoạt môi trường ảo (khuyến nghị)
python -m venv env
.\env\Scripts\activate  # Trên Windows
source env/bin/activate  # Trên Linux/Mac

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

## Cấu hình

### Tạo file .env

Tạo một file `.env` trong thư mục gốc của dự án với nội dung sau:

```
GOOGLE_API_KEY=your_google_api_key
SERVICE_API_KEY=your_service_api_key
```

Trong đó:
- `GOOGLE_API_KEY`: API key của Google AI (Gemini) - bắt buộc để sử dụng dịch vụ dịch thuật
- `SERVICE_API_KEY`: API key tùy chọn để bảo vệ API của bạn (nếu không đặt, xác thực sẽ bị vô hiệu hóa)

### Lấy Google API Key

1. Truy cập [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Đăng nhập bằng tài khoản Google của bạn
3. Tạo API key mới
4. Sao chép API key và thêm vào file `.env`

## Chạy API

### Chạy trực tiếp

```bash
python main.py
```

API sẽ chạy tại địa chỉ http://localhost:8000

### Chạy với Uvicorn (tùy chọn)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Sử dụng API

### Endpoint dịch thuật

- **URL**: `/translate`
- **Method**: `POST`
- **Authentication**: API key trong header `X-API-Key` (nếu đã cấu hình `SERVICE_API_KEY`)

### Endpoint kiểm tra trạng thái

- **URL**: `/health`
- **Method**: `GET`
- **Mô tả**: Kiểm tra xem API có hoạt động không

### Tài liệu API tự động

- **URL**: `/docs`
- **Method**: `GET`
- **Mô tả**: Tài liệu Swagger UI tự động được tạo bởi FastAPI

## Các tham số và mô hình dữ liệu

### Yêu cầu dịch (TranslationRequest)

```json
{
  "text": "Văn bản cần dịch",
  "target_language": "en",
  "source_language": "vi",
  "context": "Ngữ cảnh về văn bản (tùy chọn)"
}
```

Trong đó:
- `text`: Văn bản cần dịch (bắt buộc)
- `target_language`: Ngôn ngữ đích, có thể là mã ngôn ngữ (ví dụ: "en") hoặc tên đầy đủ (ví dụ: "English") (bắt buộc)
- `source_language`: Ngôn ngữ nguồn, có thể là mã ngôn ngữ hoặc tên đầy đủ (tùy chọn, nếu không cung cấp sẽ tự động phát hiện)
- `context`: Ngữ cảnh về văn bản để cải thiện chất lượng dịch (tùy chọn)

### Phản hồi dịch (TranslationResponse)

```json
{
  "translated_text": "Translated text",
  "model_used": "gemini-pro"
}
```

Trong đó:
- `translated_text`: Văn bản đã được dịch
- `model_used`: Tên mô hình được sử dụng để dịch

## Xử lý lỗi

API có thể trả về các mã lỗi sau:

- **403 Forbidden**: API key không hợp lệ
- **500 Internal Server Error**: Lỗi trong quá trình dịch
- **503 Service Unavailable**: Dịch vụ dịch không khả dụng (thường do vấn đề với LLM)

## Ví dụ

### Ví dụ sử dụng cURL

```bash
curl -X POST "http://localhost:8000/translate" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_service_api_key" \
  -d '{
    "text": "Xin chào thế giới",
    "target_language": "en",
    "source_language": "vi",
    "context": "Lời chào thông thường"
  }'
```

### Ví dụ sử dụng Python với requests

```python
import requests

url = "http://localhost:8000/translate"
headers = {
    "Content-Type": "application/json",
    "X-API-Key": "your_service_api_key"
}
data = {
    "text": "Xin chào thế giới",
    "target_language": "en",
    "source_language": "vi",
    "context": "Lời chào thông thường"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Ví dụ phản hồi thành công

```json
{
  "translated_text": "Hello world",
  "model_used": "gemini-pro"
}
```

### Kiểm tra trạng thái API

```bash
curl http://localhost:8000/health
```

Phản hồi:
```json
{
  "status": "ok"
}
```

## Các ngôn ngữ được hỗ trợ

API hỗ trợ các ngôn ngữ sau (có thể mở rộng trong file `main.py`):

- Tiếng Anh (en, English)
- Tiếng Việt (vi, Vietnamese)
- Tiếng Pháp (fr, French)
- Tiếng Tây Ban Nha (es, Spanish)
- Tiếng Đức (de, German)

Bạn có thể thêm nhiều ngôn ngữ khác bằng cách mở rộng hàm `get_full_language_name` trong file `main.py`.
