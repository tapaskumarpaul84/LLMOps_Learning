from fastapi import FastAPI,UploadFile,File,Form,HTTPException,Request
from fastapi.responses import JSONResponse,HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from typing import Dict,List,Any,Optional
from pathlib import Path
import os
from src.document_analyzer.data_analysis import DocumentAnalyzer
from src.document_ingestion.data_ingestion import DocHandler,DocumentComparator,ChatIngestor
from src.document_compare.document_comparator import DocumentComparatorLLM
from src.document_chat.retrieval import ConversationalRAG
from utils.document_ops import FastAPIFileAdapter,read_pdf_via_handler


FAISS_BASE = os.getenv("FAISS_BASE", "faiss_index")
UPLOAD_BASE = os.getenv("UPLOAD_BASE", "data")
FAISS_INDEX_NAME = os.getenv("FAISS_INDEX_NAME", "index")  # <--- keep consistent with save_local()

app = FastAPI(title="Document Portal API", version="0.1")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    resp = templates.TemplateResponse("index.html", {"request": request})
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok", "service": "document-portal"}

@app.post("/analyze")
async def analyze_document(file: UploadFile=File(...))-> Any:
    try:
        dh=DocHandler()
        saved_path=dh.save_pdf(FastAPIFileAdapter(file))
        text=read_pdf_via_handler(dh,saved_path)

        analyzer=DocumentAnalyzer()
        result=analyzer.analyze_document(text)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Analysis failed : {e}")
    
@app.post("/compare")
async def compare_documents(reference: UploadFile=File(...),actual: UploadFile=File(...))-> Any:
    try:
        dc=DocumentComparator()
        ref_path,act_path=dc.save_uploaded_files(FastAPIFileAdapter(reference),FastAPIFileAdapter(actual))
        _=ref_path,act_path
        combined_text=dc.combine_documents()
        comp=DocumentComparatorLLM()
        df=comp.compare_documents(combined_text)
        return {"rows": df.to_dict(orient='records'),"session_id":dc.session_id}
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Document comparison failed: {e}")
    
@app.post("/chat/index")
async def chat_build_index(
    files: List[UploadFile]=File(...),
    session_id: Optional[str] = Form(None),
    use_session_dirs: bool=Form(True),
    chunk_size : int = Form(1000),
    chunk_overlap : int = Form(100),
    k: int=Form(5)
) ->Any:
    try:
        wrapped=[FastAPIFileAdapter(f) for f in files]
        ci=ChatIngestor(
            temp_base=UPLOAD_BASE,
            faiss_base=FAISS_BASE,
            use_session_dirs=use_session_dirs,
            session_id=session_id or None
        )
        ci.built_retriever(wrapped,chunk_size=chunk_size,chunk_overlap=chunk_overlap,k=k)
        return {"session_id":ci.session_id,"k":k,"use_session_dirs":use_session_dirs}
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Indexing failed: {e}")
    
@app.post("/chat/query")
async def chat_query(
    question : str=Form(...),
    session_id: Optional[str]=Form(None),
    use_session_dirs :bool=Form(True),
    k: int=Form(5)
)->Any:
    try:
        if use_session_dirs and not session_id:
            raise HTTPException(status_code=400, detail="session_id is required when use_session_dirs=True")
        
        index_dir=os.path.join(FAISS_BASE,session_id) if use_session_dirs else FAISS_BASE
        if not os.path.isdir(index_dir):
            raise HTTPException(status_code=404,details=f"Faiss_index not found at : {index_dir}")
        
        rag=ConversationalRAG(session_id=session_id)
        rag.load_retriever_from_faiss(index_dir)

        response=rag.invoke(question,chat_history=[])

        return {
            "answer": response,
            "session_id":session_id,
            "k":k,
            "engine": "LCEL-RAG"
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Query failed: {e}")
    

# command for run uvicorn

# uvicorn app.main:app --reload
