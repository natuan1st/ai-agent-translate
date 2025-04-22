# LangChain Translation Service

A microservice using FastAPI and LangChain (with Gemini) for text translation.

## Features

- Text translation using Google's Gemini model
- API key authentication
- Support for source and target language specification
- Context-aware translations

## Setup

1. Clone the repository
2. Create a virtual environment and activate it:
   ```
   python -m venv env
   .\env\Scripts\activate  # On Windows
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your API keys:
   ```
   GOOGLE_API_KEY=your_google_api_key
   SERVICE_API_KEY=your_service_api_key
   ```

## Running the Service

```
python main.py
```

The service will be available at http://localhost:8000

## API Endpoints

- `POST /translate` - Translate text
- `GET /health` - Health check endpoint

## Running Tests

To run the tests, make sure you have pytest installed:

```
pip install pytest pytest-asyncio
```

Then run:

```
python -m pytest
```

## Test Coverage

The test suite covers:

- Authentication with API keys
- Successful translation with various parameters
- Error handling scenarios
- Language code mapping
- Edge cases