# Assignment Generator - New Features

## Overview
The Assignment Generator has been completely redesigned with modern UI and powerful new features.

## New Features

### 1. Dual Input Modes

#### Voice Input Mode 🎤
- Click-to-speak voice recognition
- Real-time speech-to-text transcription
- Visual feedback with animated voice bubble
- Perfect for quickly describing assignment requirements
- Automatically processes voice input into assignment content

#### Manual Input Mode ✍️
- Traditional form-based input
- File upload support (PDF, Word, PowerPoint)
- Text content input
- Custom structure builder
- Full control over assignment parameters

### 2. RAG (Retrieval-Augmented Generation) Toggle 📚

**What is RAG?**
- RAG allows the AI to reference your uploaded study materials when generating assignments
- The AI will read through your materials and incorporate relevant information
- Provides more accurate and contextual responses

**How to Use:**
1. Upload study materials in the "My Materials" section
2. When creating an assignment, enable the "Use Study Materials" toggle
3. The AI will automatically reference your materials during generation
4. See which materials were used in the assignment result

**Benefits:**
- More accurate assignments based on your course materials
- Consistent with your study content
- Better quality outputs
- Personalized to your learning materials

### 3. Assignment Structure Builder 📐
- Add custom sections to your assignment
- Define the structure you want
- Remove or reorder sections
- Perfect for structured essays and reports

### 4. Multiple Output Formats
- Microsoft Word (.docx)
- PowerPoint (.pptx)
- PDF Document (.pdf)
- Plain Text

### 5. Task Types
- Write an Essay
- Summarize
- Answer Questions
- Generate Slides
- Provide Structured Answers

## How to Use

### Creating an Assignment with Voice:
1. Go to Assignment → New Assignment
2. Select "Voice Input" mode
3. Click the microphone button
4. Speak your assignment requirements
5. Enable "Use Study Materials" if you want AI to reference your uploads
6. Click "Generate Assignment"

### Creating an Assignment Manually:
1. Go to Assignment → New Assignment
2. Select "Manual Input" mode
3. Enter assignment title
4. Upload a file OR enter text content
5. Choose task type and output format
6. Optionally add structure sections
7. Enable/disable "Use Study Materials" toggle
8. Click "Generate Assignment"

### Viewing Results:
1. Go to "My Assignments" to see all generated assignments
2. Click "View" to see the result
3. Download in your chosen format
4. See which study materials were referenced

## Technical Details

### RAG Implementation
- Fetches user's uploaded study materials
- Extracts text content from materials
- Builds context for AI prompt
- AI references materials when generating content
- Tracks which materials were used

### Voice Recognition
- Uses Web Speech API
- Supports continuous speech recognition
- Real-time transcription
- Works in Chrome and Edge browsers

### File Processing
- Supports PDF, Word, PowerPoint uploads
- Extracts text from uploaded files
- Processes both file and text content
- Generates output in multiple formats

## Database Changes
- Added `use_rag` field to Assignment model
- Tracks whether RAG was enabled for each assignment
- Stores which materials were used in AssignmentResult

## API Endpoints
- `/materials/api/count/` - Get count of user's study materials

## UI Theme
- Modern black and white design
- Matches site-wide theme
- Responsive layout
- Smooth animations and transitions
- Toggle switches for options

## Future Enhancements
- Support for more file formats
- Advanced structure templates
- Collaborative assignments
- Assignment history and analytics
- Export to more formats
