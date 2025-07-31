from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA
from langchain_ollama import OllamaLLM
from typing import Optional, List, Any, Dict
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGAgent:
    """
    Simple RAG Agent using LangChain, ChromaDB and Llama 3.2 via Ollama
    """
    
    def __init__(self):
        self.vectorstore = None
        self.qa_chain = None
        
        # Initialize embeddings
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Initialize Llama 3.2 via Ollama
        self.llm = OllamaLLM(
            model="llama3.2",
            temperature=0.1
        )
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        
        logger.info("RAG Agent initialized successfully")
    
    def load_document(self, pdf_path: str) -> None:
        """
        Load and process PDF document
        """
        try:
            logger.info(f"Loading document: {pdf_path}")
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
            # Load PDF
            loader = PyPDFLoader(pdf_path)
            pages = loader.load()
            
            if not pages:
                raise ValueError("No content found in PDF")
            
            logger.info(f"Loaded {len(pages)} pages from PDF")
            
            # Split text into chunks
            texts = self.text_splitter.split_documents(pages)
            logger.info(f"Document split into {len(texts)} chunks")
            
            # Create vector store with ChromaDB
            self.vectorstore = Chroma.from_documents(
                documents=texts,
                embedding=self.embeddings,
                persist_directory="./chroma_db"
            )
            
            logger.info("Vector store created successfully")
            
            # Create QA chain
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.vectorstore.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 3}
                ),
                return_source_documents=True
            )
            
            logger.info("QA chain created successfully")
            
        except Exception as e:
            logger.error(f"Error loading document: {e}")
            raise Exception(f"Failed to load document: {str(e)}")
    
    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Answer a question using RAG
        """
        try:
            if not self.qa_chain:
                raise ValueError("No document loaded. Please load a document first.")
            
            logger.info(f"Answering question: {question[:50]}...")
            
            # Create enhanced prompt
            enhanced_prompt = f"""
            Based on the provided document context, please answer the following question accurately and concisely.
            If the information is not available in the context, please state that clearly.
            
            Question: {question}
            
            Please provide a clear, factual answer based only on the information available in the document.
            """
            
            # Get answer from QA chain
            result = self.qa_chain.invoke({"query": enhanced_prompt})
            
            answer_text = result["result"]
            source_docs = result.get("source_documents", [])
            
            # Calculate confidence based on source document relevance
            confidence = self._calculate_confidence(question, source_docs)
            
            logger.info("Question answered successfully")
            
            return {
                "answer": self._clean_answer(answer_text),
                "confidence": confidence,
                "source_count": len(source_docs),
                "sources": [doc.page_content[:200] + "..." for doc in source_docs[:2]]
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "confidence": 0.0,
                "source_count": 0,
                "sources": []
            }
    
    def _calculate_confidence(self, question: str, source_docs: List[Any]) -> float:
        """
        Calculate confidence score based on source document relevance
        """
        if not source_docs:
            return 0.0
        
        # Simple confidence calculation based on number of relevant sources
        # and basic keyword matching
        question_words = set(question.lower().split())
        total_overlap = 0
        
        for doc in source_docs:
            doc_words = set(doc.page_content.lower().split())
            overlap = len(question_words.intersection(doc_words))
            total_overlap += overlap
        
        # Normalize confidence score
        max_possible_overlap = len(question_words) * len(source_docs)
        if max_possible_overlap > 0:
            confidence = min(total_overlap / max_possible_overlap, 1.0)
        else:
            confidence = 0.0
        
        # Boost confidence if we have multiple relevant sources
        if len(source_docs) >= 2:
            confidence = min(confidence * 1.2, 1.0)
        
        return round(confidence, 2)
    
    def _clean_answer(self, answer: str) -> str:
        """
        Clean and format the answer text
        """
        # Remove common LLM artifacts and clean up formatting
        answer = answer.strip()
        
        # Remove redundant phrases
        redundant_phrases = [
            "Based on the provided context,",
            "According to the document,",
            "The document states that",
            "From the information provided,",
            "Based on the provided document context,",
        ]
        
        for phrase in redundant_phrases:
            if answer.lower().startswith(phrase.lower()):
                answer = answer[len(phrase):].strip()
        
        # Ensure proper capitalization
        if answer and answer[0].islower():
            answer = answer[0].upper() + answer[1:]
        
        return answer
    
    def get_vectorstore_info(self) -> Dict[str, Any]:
        """
        Get information about the current vector store
        """
        if not self.vectorstore:
            return {"status": "No document loaded"}
        
        try:
            return {
                "status": "Document loaded",
                "embeddings_model": "sentence-transformers/all-MiniLM-L6-v2",
                "chunk_size": 1000,
                "chunk_overlap": 200,
                "vectorstore_type": "ChromaDB",
                "llm_model": "llama3.2"
            }
        except Exception as e:
            return {"status": f"Error getting info: {str(e)}"}
    
    def cleanup(self):
        """
        Clean up resources
        """
        if self.vectorstore:
            try:
                # ChromaDB cleanup if needed
                pass
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
        logger.info("RAG Agent cleaned up")