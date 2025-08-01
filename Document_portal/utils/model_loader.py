import os
import sys
from dotenv import load_dotenv
from utils.config_loader import load_config
from logger import custom_logger
from exceptions.custom_exception import DocumentPortalException
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import ChatOpenAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

log=custom_logger.CustomLogger().get_logger(__name__)

class ModelLoader:
    """Configure embedding models and LLM."""
    def __init__(self):
        load_dotenv()
        self._validate_env()
        self.config=load_config()
        log.info("Cufiguration loaded successfully", config_keys=list(self.config.keys()))
    def _validate_env(self):
        """
        validate necessary environment variables.
        Ensure that API keys are exist.
        """
        required_vars=["GOOGLE_API_KEY","GROQ_API_KEY"]
        self.api_keys={key:os.getenv(key) for key in required_vars}
        missing=[k for k,v in self.api_keys.items() if not v]

        if missing:
            log.error("Missing environment variables",missing_vars=missing)
            raise DocumentPortalException("Missing Environment Variables",sys)
        log.info("Environment variables validated",available_keys=[k for k in self.api_keys if self.api_keys[k]])
    def load_embeddings(self):
        """
        Load and return the embedding model.
        """
        try:
            log.info("Loading embedding model....")
            model_name=self.config["embedding_model"]["google"]["model_name"]
            return GoogleGenerativeAIEmbeddings(model=model_name)
        except Exception as e:
            log.error("Error in loading Embedding model",error=str(e))
            raise DocumentPortalException("Failed to load embedding model",sys)
    def load_llm(self):
        """
        Load and return the LLM , LLM will be load dynamically.
        """
        llm_block=self.config["llm"]

        log.info("Loading LLM...")

        provider_key=os.getenv("LLM_PROVIDER",'google')

        if provider_key not in llm_block:
            log.error("LLM provider not found in config",provider_key=provider_key)
            raise ValueError(f"Provider '{provider_key}' not found in config.")
        
        llm_config=llm_block[provider_key]
        provider=llm_config.get("provider")
        model_name=llm_config.get("model_name")
        temperature=llm_config.get("temperature",0.2)
        max_tokens=llm_config.get("max_output_tokens",2048)

        log.info("Loading LLM",provider=provider,model=model_name,temperature=temperature,max_tokens=max_tokens)
        if provider=='google':
            llm=ChatGoogleGenerativeAI(
                model=model_name,
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            return llm
        elif provider=='groq':
            llm=ChatGroq(
                model=model_name,
                api_key=self.api_keys["GROQ_API_KEY"],
                temperature=temperature
            )
            return llm
        elif provider=='openai':
            llm=ChatOpenAI(
                model=model_name,
                api_key=self.api_keys["OPENAI_API_KEY"],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return llm
        else:
            log.error("Unsupported LLM provider",provider=provider)
            raise ValueError(f"Unsupported LLM provider: {provider}")

if __name__=="__main__":
    loader=ModelLoader()

    embedding=loader.load_embeddings()
    print("Embedding model loaded ",embedding)

    llm=loader.load_llm()
    print(f"LLM loaded: {llm}")

    result=llm.invoke("Hello, How are you?")
    print(result.content)

