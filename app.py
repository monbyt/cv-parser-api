import os
import tempfile
from typing import Dict, Any, List, Optional, Union
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, create_model
import uvicorn
import asyncio
import PyPDF2
from cerebras.cloud.sdk import Cerebras
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CV Parser API",
    description="API service to extract structured information from CVs in PDF format",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Generic flexible model that can handle any structure
class FlexibleModel(BaseModel):
    class Config:
        extra = "allow"  # Allow extra fields not defined in the model

    def __init__(self, **data):
        # Convert any nested dictionaries to FlexibleModels
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = FlexibleModel(**value)
            elif isinstance(value, list):
                data[key] = [
                    FlexibleModel(**item) if isinstance(item, dict) else item
                    for item in value
                ]
        super().__init__(**data)

    def dict(self, *args, **kwargs):
        # Convert back to dict for JSON serialization
        result = super().dict(*args, **kwargs)
        return result

# Use this as the response model
class CVParseResponse(FlexibleModel):
    pass

# Check if Cerebras API key is set
if not os.environ.get("CEREBRAS_API_KEY"):
    logger.warning("CEREBRAS_API_KEY environment variable not set. Using mock data for responses.")

# Function to extract text from PDF files using PyPDF2
async def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Asynchronously extracts text content from a PDF file.
    
    Args:
        file_content: Raw bytes of the PDF file
        
    Returns:
        Extracted text as a string
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name

        text = ""
        with open(temp_file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text()
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        return text
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")

async def parse_cv_with_llm(cv_text: str) -> Dict[str, Any]:
    """Parse CV text using LLM to extract structured information."""
    try:
        # Check if Cerebras API key is set
        if not os.environ.get("CEREBRAS_API_KEY"):
            # Return mock data for testing without API key
            return {
                "name": "John Doe",
                "summary": "Experienced software engineer with 5+ years in web development",
                "contact": {
                    "email": "john.doe@example.com",
                    "phone": "+1234567890",
                    "linkedin": "linkedin.com/in/johndoe",
                    "github": "github.com/johndoe",
                    "website": "johndoe.com"
                },
                "education": [
                    {
                        "institution": "University of Example",
                        "degree": "Bachelor of Science",
                        "field_of_study": "Computer Science",
                        "start_date": "2015",
                        "end_date": "2019"
                    }
                ],
                "experience": [
                    {
                        "company": "Tech Company Inc.",
                        "position": "Senior Software Engineer",
                        "start_date": "2020",
                        "end_date": "Present",
                        "description": "Developed and maintained web applications using React and Node.js"
                    }
                ],
                "skills": [
                    {"name": "JavaScript", "level": "Expert"},
                    {"name": "Python", "level": "Intermediate"},
                    {"name": "React", "level": "Advanced"}
                ],
                "languages": ["English (Native)", "Spanish (Intermediate)"],
                "certifications": ["AWS Certified Developer", "Scrum Master"]
            }

        # Initialize Cerebras client
        client = Cerebras(api_key=os.environ.get("CEREBRAS_API_KEY"))
        
        # Create the prompt
        prompt = f"""
        You are an expert CV parser. Extract ALL important information from the following CV text.
        Analyze the CV thoroughly and identify ALL relevant sections and details.

        Return a RFC8259 compliant JSON object that captures the complete structure of the CV.
        Do not limit yourself to predefined sections - extract whatever sections and information are present in the CV.

        Common sections might include (but are not limited to):
        - Personal information (name, contact details)
        - Summary or objective
        - Work experience
        - Education
        - Skills or competencies
        - Projects
        - Publications
        - Certifications
        - Languages
        - Volunteer work
        - Awards and honors
        - References
        - Additional sections specific to this CV

        For each section, capture all relevant details in a structured format.
        Ensure your response is ONLY valid JSON with no additional text or explanation.

        CV Text:
        {cv_text}
        """
        
        # Generate response using Cerebras
        chat_completion = client.chat.completions.create(
            model="llama3.1-8b",  # or "llama-3.3-70b" if you prefer
            messages=[
                {"role": "system", "content": "You are an expert CV parser that outputs only valid JSON."},
                {"role": "user", "content": prompt}
            ],
        )
        
        # Extract the JSON content from the response
        content = chat_completion.choices[0].message.content
        
        # Convert string to dictionary if needed
        if isinstance(content, str):
            import json
            try:
                content = json.loads(content)
            except json.JSONDecodeError:
                # If the response is not valid JSON, try to extract JSON part
                import re
                json_match = re.search(r'```json\n(.*?)\n```', content, re.DOTALL)
                if json_match:
                    content = json.loads(json_match.group(1))
                else:
                    # Try another pattern without language specification
                    json_match = re.search(r'```\n(.*?)\n```', content, re.DOTALL)
                    if json_match:
                        content = json.loads(json_match.group(1))
                    else:
                        # Try to find JSON-like content with curly braces
                        json_match = re.search(r'\{.*\}', content, re.DOTALL)
                        if json_match:
                            content = json.loads(json_match.group(0))
                        else:
                            raise HTTPException(status_code=500, detail="Failed to parse LLM response as JSON")
        
        return content
    
    except Exception as e:
        logger.error(f"Error parsing CV with LLM: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error parsing CV with LLM: {str(e)}")

@app.post("/parse-cv")
async def parse_cv(file: UploadFile = File(...)):
    """
    Parse a CV in PDF format and extract structured information.
    
    - **file**: PDF file containing the CV
    
    Returns a structured JSON representation of the CV information.
    """
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Read file content
    file_content = await file.read()
    
    # Extract text from PDF
    cv_text = await extract_text_from_pdf(file_content)
    
    # Parse CV text with LLM
    try:
        parsed_data = await parse_cv_with_llm(cv_text)
        
        # Return the data directly without validation constraints
        return parsed_data
    except Exception as e:
        logger.error(f"Error processing CV: {str(e)}")
        # Return a more specific error message based on where the failure occurred
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process CV: {str(e)}. Please ensure the PDF is valid and not corrupted."
        )

@app.get("/health")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True) 