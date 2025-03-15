# CV Parser API Service

A FastAPI service that extracts structured information from CVs in PDF format using Cerebras AI with the Llama-3.3-70b model.

## Features

- PDF parsing to extract text content
- LLM-powered information extraction using Cerebras AI's Llama-3.3-70b model
- Flexible JSON output that adapts to any CV structure
- Asynchronous processing for improved performance
- Containerized deployment with Docker
- Comprehensive error handling

## Prerequisites

- Python 3.8+
- Docker (optional, for containerized deployment)
- Cerebras API key (set as environment variable)

## Installation

### Local Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/monbyt/cv-parser-api.git
   cd cv-parser-api
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set your Cerebras API key:
   ```bash
   export CEREBRAS_API_KEY=your_api_key_here
   ```

5. Run the application:
   ```bash
   uvicorn app:app --reload
   ```

### Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t cv-parser-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 -e CEREBRAS_API_KEY=your_api_key_here cv-parser-api
   ```

## API Usage

### Parse CV Endpoint

**URL**: `/parse-cv`
**Method**: `POST`
**Content-Type**: `multipart/form-data`

**Request**:
- `file`: PDF file containing the CV

**Response**:
A flexible JSON structure containing all important information extracted from the CV. The structure adapts to the content of each CV rather than forcing a predefined format.

Example response:
```json
{
  "PersonalInformation": {
    "Name": "John Doe",
    "ContactDetails": [
      { "Email": "john.doe@example.com" },
      { "Phone": "+1234567890" }
    ],
    "Location": "New York, USA"
  },
  "Education": {
    "University of Example": {
      "Degree": "BSc in Computer Science",
      "GraduationYear": "2020"
    }
  },
  "WorkExperience": {
    "Example Company": {
      "Role": "Software Engineer",
      "Duration": "2020-Present",
      "Responsibilities": [
        "Developed web applications using React",
        "Implemented CI/CD pipelines"
      ]
    }
  },
  "Skills": {
    "Programming": ["Python", "JavaScript", "Java"],
    "Frameworks": ["React", "Django", "Spring Boot"],
    "Tools": ["Git", "Docker", "AWS"]
  },
  "Languages": {
    "English": "Native",
    "Spanish": "Fluent"
  }
}
```

### Health Check Endpoint

**URL**: `/health`
**Method**: `GET`

**Response**:
```json
{
  "status": "healthy"
}
```

## Implementation Details

### Flexible Parsing Approach

The service uses a flexible approach to CV parsing:

1. **No Predefined Structure**: Instead of forcing CVs into a rigid template, the parser adapts to whatever sections and information are present in each CV.

2. **LLM-Powered Extraction**: The Cerebras Llama-3.3-70b model analyzes the CV text and identifies all relevant information.

3. **Dynamic Response Format**: The API returns a JSON structure that matches the natural organization of the CV, preserving hierarchical relationships and section groupings.

4. **Asynchronous Processing**: All operations (file reading, text extraction, LLM processing) are handled asynchronously for better performance.

### Error Handling

The service includes comprehensive error handling:
- Validation of file format (PDF only)
- Graceful handling of PDF parsing errors
- Fallback to mock data if no API key is provided
- Detailed error messages for troubleshooting

## API Documentation

Once the server is running, you can access the auto-generated API documentation:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Notes

- If the `CEREBRAS_API_KEY` environment variable is not set, the API will return mock data for testing purposes.
- The service currently only supports PDF files.
- For production deployment, consider adding authentication and rate limiting.