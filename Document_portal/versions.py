import importlib.metadata

packages=[
    "langchain",
    "python-dotenv",
    "ipykernel",
    "langchain_groq",
    "langchain_google_genai",
    "langchain-community",
    "faiss-cpu",
    "structlog",
    "PyMuPDF",
    "langchain-core",
    "pytest",
    "streamlit",
    "fastapi",
    "uvicorn",
    "python-multipart",
    "docx2txt",
    "pypdf",
    "langchain_huggingface",
    "langchain_openai",
    "pydantic",
    "pathlib",
    "langchain_text_splitters"
]

for pkg in packages:
    try:
        version=importlib.metadata.version(pkg)
        print(f"{pkg}=={version}")
    except importlib.metadata.PackageNotFoundError:
        print(f"{pkg} not installed")