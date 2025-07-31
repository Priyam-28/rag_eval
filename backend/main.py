import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
from typing import Dict, Any
from rag_agent import RAGAgent
from utils import calculate_similarity_score, parse_json_file, validate_questions_format, validate_answers_format
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="PDF RAG API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global RAG agent instance
rag_agent = None

@app.on_event("startup")
async def startup_event():
    """Initialize RAG agent on startup"""
    global rag_agent
    try:
        rag_agent = RAGAgent()
        logger.info("RAG Agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG Agent: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global rag_agent
    if rag_agent:
        rag_agent.cleanup()

@app.get("/")
async def root():
    return {"message": "PDF RAG API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent_status": "initialized" if rag_agent else "not initialized"
    }

@app.post("/upload-pdf")
async def upload_pdf(pdf: UploadFile = File(...)):
    """
    Upload and process PDF document
    """
    global rag_agent
    
    if not rag_agent:
        raise HTTPException(status_code=500, detail="RAG agent not initialized")
    
    try:
        # Validate file type
        if pdf.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Save uploaded PDF temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp:
            pdf_content = await pdf.read()
            pdf_temp.write(pdf_content)
            pdf_path = pdf_temp.name
        
        try:
            # Process PDF with RAG agent
            rag_agent.load_document(pdf_path)
            
            return {
                "status": "success",
                "message": "PDF processed successfully",
                "filename": pdf.filename,
                "info": rag_agent.get_vectorstore_info()
            }
            
        finally:
            # Cleanup temporary file
            if os.path.exists(pdf_path):
                os.unlink(pdf_path)
    
    except Exception as e:
        logger.error(f"Error processing PDF: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/ask-question")
async def ask_question(request: Dict[str, str]):
    """
    Ask a single question to the loaded document
    """
    global rag_agent
    
    if not rag_agent:
        raise HTTPException(status_code=500, detail="RAG agent not initialized")
    
    try:
        question = request.get("question", "").strip()
        if not question:
            raise HTTPException(status_code=400, detail="Question is required")
        
        # Get answer from RAG agent
        result = rag_agent.answer_question(question)
        
        return {
            "status": "success",
            "question": question,
            "answer": result["answer"],
            "confidence": result["confidence"],
            "source_count": result["source_count"],
            "sources": result["sources"]
        }
    
    except Exception as e:
        logger.error(f"Error answering question: {e}")
        raise HTTPException(status_code=500, detail=f"Error processing question: {str(e)}")

@app.post("/process-rag")
async def process_rag(
    pdf: UploadFile = File(...),
    questions: UploadFile = File(...)
):
    """
    Process PDF document and answer multiple questions using RAG
    """
    global rag_agent
    
    if not rag_agent:
        raise HTTPException(status_code=500, detail="RAG agent not initialized")
    
    try:
        # Validate file types
        if pdf.content_type != "application/pdf":
            raise HTTPException(status_code=400, detail="PDF file required")
        
        if not questions.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="JSON file required for questions")

        # Save uploaded files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as pdf_temp:
            pdf_content = await pdf.read()
            pdf_temp.write(pdf_content)
            pdf_path = pdf_temp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as questions_temp:
            questions_content = await questions.read()
            questions_temp.write(questions_content)
            questions_path = questions_temp.name

        try:
            # Parse questions
            questions_data = parse_json_file(questions_path)
            
            if not validate_questions_format(questions_data):
                raise HTTPException(status_code=400, detail="Invalid questions format. Expected: {'questions': [{'question': 'text'}]}")

            # Process PDF with RAG agent
            rag_agent.load_document(pdf_path)
            
            # Generate answers
            answers = []
            for i, q in enumerate(questions_data["questions"]):
                question_text = q.get("question", "").strip()
                if question_text:
                    answer_data = rag_agent.answer_question(question_text)
                    answers.append({
                        "id": q.get("id", f"q_{i+1}"),
                        "question": question_text,
                        "answer": answer_data["answer"],
                        "confidence": answer_data.get("confidence", 0.0),
                        "source_count": answer_data.get("source_count", 0)
                    })

            return {
                "status": "success",
                "answers": answers,
                "total_questions": len(answers),
                "pdf_info": rag_agent.get_vectorstore_info()
            }

        finally:
            # Cleanup temporary files
            for path in [pdf_path, questions_path]:
                if os.path.exists(path):
                    os.unlink(path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in process_rag: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")

@app.post("/score-answers")
async def score_answers(
    questions: UploadFile = File(...),
    expected_answers: UploadFile = File(...)
):
    """
    Score RAG answers against expected answers
    """
    global rag_agent
    
    if not rag_agent:
        raise HTTPException(status_code=500, detail="RAG agent not initialized")
    
    try:
        # Validate file types
        if not questions.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="JSON file required for questions")
        
        if not expected_answers.filename.endswith('.json'):
            raise HTTPException(status_code=400, detail="JSON file required for expected answers")

        # Save uploaded files temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as questions_temp:
            questions_content = await questions.read()
            questions_temp.write(questions_content)
            questions_path = questions_temp.name

        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as answers_temp:
            answers_content = await expected_answers.read()
            answers_temp.write(answers_content)
            answers_path = answers_temp.name

        try:
            # Parse files
            questions_data = parse_json_file(questions_path)
            expected_data = parse_json_file(answers_path)

            if not validate_questions_format(questions_data):
                raise HTTPException(status_code=400, detail="Invalid questions format")
            
            if not validate_answers_format(expected_data):
                raise HTTPException(status_code=400, detail="Invalid expected answers format")

            # Create question-answer mapping
            expected_map = {}
            for answer in expected_data["answers"]:
                question_id = answer.get("id", "")
                expected_map[question_id] = answer.get("expected_answer", "")

            scored_answers = []
            
            # Process each question
            for i, q in enumerate(questions_data["questions"]):
                question_id = q.get("id", f"q_{i+1}")
                question_text = q.get("question", "").strip()
                expected_answer = expected_map.get(question_id, "")
                
                if expected_answer and question_text:
                    # Generate RAG answer
                    rag_response = rag_agent.answer_question(question_text)
                    rag_answer = rag_response["answer"]
                    
                    # Calculate similarity score
                    score = calculate_similarity_score(expected_answer, rag_answer)
                    
                    # Determine status
                    if score >= 0.8:
                        status = "excellent"
                    elif score >= 0.6:
                        status = "good"
                    else:
                        status = "poor"
                    
                    scored_answers.append({
                        "id": question_id,
                        "question": question_text,
                        "expected_answer": expected_answer,
                        "rag_answer": rag_answer,
                        "score": score,
                        "status": status,
                        "confidence": rag_response.get("confidence", 0.0)
                    })

            # Calculate overall metrics
            total_questions = len(scored_answers)
            if total_questions == 0:
                raise HTTPException(status_code=400, detail="No valid question-answer pairs found")
            
            average_score = sum(item["score"] for item in scored_answers) / total_questions
            
            excellent_count = sum(1 for item in scored_answers if item["status"] == "excellent")
            good_count = sum(1 for item in scored_answers if item["status"] == "good")
            poor_count = sum(1 for item in scored_answers if item["status"] == "poor")

            return {
                "status": "success",
                "scored_answers": scored_answers,
                "metrics": {
                    "total_questions": total_questions,
                    "average_score": round(average_score, 3),
                    "excellent_count": excellent_count,
                    "good_count": good_count,
                    "poor_count": poor_count,
                    "pass_rate": round((excellent_count + good_count) / total_questions * 100, 1)
                }
            }

        finally:
            # Cleanup temporary files
            for path in [questions_path, answers_path]:
                if os.path.exists(path):
                    os.unlink(path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in score_answers: {e}")
        raise HTTPException(status_code=500, detail=f"Scoring error: {str(e)}")

@app.get("/agent-info")
async def get_agent_info():
    """
    Get information about the current RAG agent state
    """
    global rag_agent
    
    if not rag_agent:
        return {"status": "RAG agent not initialized"}
    
    return rag_agent.get_vectorstore_info()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)