import os
import logging
import re
import urllib.parse
from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Configuration ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY") # API key for this service



if not GOOGLE_API_KEY:
    logger.error("GOOGLE_API_KEY not found in environment variables.")
    # You might want to raise an exception or exit here in a real application
    # raise ValueError("GOOGLE_API_KEY not found")

if not SERVICE_API_KEY:
    logger.warning("SERVICE_API_KEY not found in environment variables. Authentication will be disabled.")

# --- API Key Authentication ---
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def get_api_key(api_key: str = Security(api_key_header)):
    if not SERVICE_API_KEY: # If no service key is set, disable auth
        return
    if api_key == SERVICE_API_KEY:
        return api_key
    else:
        raise HTTPException(
            status_code=403,
            detail="Could not validate credentials",
        )

# --- Pydantic Models ---
class TranslationRequest(BaseModel):
    text: str = Field(..., description="The text to be translated.")
    target_language: str = Field(..., description="The target language (e.g., 'en', 'English').")
    source_language: str | None = Field(None, description="The source language (e.g., 'vi', 'Vietnamese'). Optional.")
    context: str | None = Field(None, description="Optional context about the text.")

class TranslationResponse(BaseModel):
    translated_text: str
    model_used: str

# --- LangChain Setup ---
# Initialize the LLM (Gemini)
llm = None
if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=GOOGLE_API_KEY)
        logger.info("ChatGoogleGenerativeAI initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize ChatGoogleGenerativeAI: {e}", exc_info=True)
        # Handle initialization failure, maybe fall back or raise critical error
else:
    logger.warning("GOOGLE_API_KEY is not set. LLM functionality will be unavailable.")

# Define the prompt template
prompt_template = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a professional translator. Translate the following text from {source_language_full} to {target_language_full}. Context: {context}. Maintain an appropriate tone. DO NOT translate any placeholders that look like __PROTECTED_*__. These are special markers that will be replaced later. If you see HTML tags or encoded URIs, preserve their exact structure."),
        ("human", "{text}")
    ]
)

# Define the output parser
output_parser = StrOutputParser()

# Create the translation chain using LangChain Expression Language (LCEL)
# Ensure llm is initialized before creating the chain
translation_chain = None
if llm:
    translation_chain = prompt_template | llm | output_parser
else:
    logger.error("LLM not initialized. Translation chain cannot be created.")

# Helper to get full language names (can be expanded)
def get_full_language_name(lang_code: str | None) -> str:
    mapping = {
        "en": "English",
        "vi": "Vietnamese",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        # Add more languages as needed
    }
    # Handle potential None input for lang_code
    if lang_code:
        return mapping.get(lang_code.lower(), lang_code) # Return code if not found
    return "unknown language"

# --- URI Handling Functions ---
# Regex patterns for identifying encoded URIs and HTML elements
URI_PATTERN = r'(%[0-9A-Fa-f]{2})+'
HTML_TAG_PATTERN = r'<[^>]+>'
URL_PATTERN = r'https?://[^\s]+'

def identify_special_segments(text: str) -> list:
    """Identify segments that should not be translated (URIs, HTML tags, URLs)."""
    segments = []

    # Find encoded URI segments
    for match in re.finditer(URI_PATTERN, text):
        segments.append((match.start(), match.end(), match.group(0), 'uri'))

    # Find HTML tags
    for match in re.finditer(HTML_TAG_PATTERN, text):
        segments.append((match.start(), match.end(), match.group(0), 'html'))

    # Find URLs
    for match in re.finditer(URL_PATTERN, text):
        segments.append((match.start(), match.end(), match.group(0), 'url'))

    # Sort by start position
    segments.sort(key=lambda x: x[0])
    return segments

def protect_special_segments(text: str) -> tuple[str, list]:
    """Replace special segments with placeholders to protect them during translation."""
    segments = identify_special_segments(text)
    protected_text = text
    offset = 0

    for i, (start, end, content, segment_type) in enumerate(segments):
        # Adjust positions based on previous replacements
        adj_start = start - offset
        adj_end = end - offset

        # Create a unique placeholder
        placeholder = f"__PROTECTED_{segment_type.upper()}_{i}__"

        # Replace the segment with the placeholder
        protected_text = protected_text[:adj_start] + placeholder + protected_text[adj_end:]

        # Update offset for next replacement
        offset += (end - start) - len(placeholder)

    return protected_text, segments

def restore_special_segments(translated_text: str, original_segments: list) -> str:
    """Restore protected segments in the translated text."""
    result = translated_text

    for i, (_, _, content, segment_type) in enumerate(original_segments):
        placeholder = f"__PROTECTED_{segment_type.upper()}_{i}__"
        result = result.replace(placeholder, content)

    return result

# --- FastAPI Application ---
app = FastAPI(
    title="LangChain Translation Service",
    description="A microservice using FastAPI and LangChain (with Gemini) for text translation.",
    version="0.1.0",
    swagger_ui_parameters={
        "syntaxHighlight": {
            "themes": ["nord", "monokai"],
            "activeTheme": "nord",
        }
    }
)

@app.post("/translate", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest, api_key: str = Depends(get_api_key)):
    """Receives text and target language, returns the translation."""
    logger.info(f"Received translation request for target language: {request.target_language}")

    if not translation_chain:
        logger.error("Translation chain is not available due to LLM initialization issues.")
        raise HTTPException(status_code=503, detail="Translation service is unavailable. LLM not configured.")

    source_lang_full = get_full_language_name(request.source_language or "auto-detect") # Default to auto-detect if not provided
    target_lang_full = get_full_language_name(request.target_language)
    context_str = request.context or "General text"

    # Protect special segments like encoded URIs, HTML tags, and URLs
    original_text = request.text
    protected_text, segments = protect_special_segments(original_text)
    logger.info(f"Protected {len(segments)} special segments in the text")

    input_data = {
        "text": protected_text,
        "source_language_full": source_lang_full,
        "target_language_full": target_lang_full,
        "context": context_str,
    }

    try:
        # Invoke the translation chain asynchronously
        translated_text = await translation_chain.ainvoke(input_data)

        # Restore the protected segments in the translated text
        if segments:
            final_text = restore_special_segments(translated_text, segments)
            logger.info("Protected segments restored in the translated text")
        else:
            final_text = translated_text

        logger.info("Translation successful.")
        # Ensure llm is not None before accessing attributes
        model_name = llm.model if llm else "unknown"
        return TranslationResponse(
            translated_text=final_text,
            model_used=model_name
        )
    except Exception as e:
        logger.error(f"Error during translation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

@app.get("/health")
def health_check():
    """Simple health check endpoint."""
    return {"status": "ok"}

# --- Run the server (for local development) ---
if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server...")
    # Make sure GOOGLE_API_KEY is available if running directly
    if not GOOGLE_API_KEY:
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please create a .env file with GOOGLE_API_KEY=YOUR_KEY")
    elif not llm:
        print("Error: LLM could not be initialized. Server cannot start translation service.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)