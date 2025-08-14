import sys
import os
from operator import itemgetter
from typing import List,Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_community.vectorstores import FAISS
from langchain_core.messages import BaseMessage

from utils.model_loader import ModelLoader
from exceptions.custom_exception import DocumentPortalException
from logger.custom_logger import CustomLogger
from model.models import PromptType
from prompts.prompt_library import PROMPT_REGISTRY


class ConversationalRAG:
    def __init__(self,session_id:str,retriever=None):
        try:
            self.log=CustomLogger().get_logger(__name__)
            self.log.info("ConversationalRAG initialization started...")
            self.session_id=session_id
            self.llm=self._load_llm()
            self.contextualize_prompt:ChatPromptTemplate=PROMPT_REGISTRY[PromptType.CONTEXTUALIZE_QUESTION.value]
            self.qa_prompt:ChatPromptTemplate=PROMPT_REGISTRY[PromptType.CONTEXT_QA.value]

            if retriever is None:
                raise ValueError("Retriever can not be None.")
            self.retriever=retriever
            self.retriever_chain=self._build_lcel_chain()

            self.log.info("ConversationalRAG initialized.",session_id=self.session_id)
        except Exception as e:
            self.log.error("ConversationalRAG initialization failed",error=str(e))
            raise DocumentPortalException("ConversationalRAG initialization failed",sys)

    def load_retriever_from_faiss(self,index_path: str):
        """Load a FAISS vectorstore from the disk and convert it to as a retriever."""
        try:
            self.log.info("Started loading retriever from the FAISS.")
            embeddings=ModelLoader().load_embeddings()
            if not os.path.isdir(index_path):
                raise FileNotFoundError(f"FAISS index directory not found: {index_path}")
            vectorstore=FAISS.load_local(index_path,embeddings,allow_dangerous_deserialization=True)

            self.retriever=vectorstore.as_retriever(search_type='similarity',search_kwargs={'k':5})
            
            self.log.info("Loaded retriever successfully",index_path=index_path,session_id=self.session_id)
            #self._build_lcel_chain()
            return self.retriever
        except Exception as e:
            self.log.error("Failed to load retriever from FAISS",error=str(e))
            raise DocumentPortalException("Failed to load retriever",sys)
    def invoke(self,user_input:str,chat_history: Optional[List[BaseMessage]]=None)->str:
        """
        Args:
            user_input(str): _description_
            chat_history (Optional[List[BaseMessage]],optional):_description_.Default to None
        """
        try:
            self.log.info("Invoke conversationalRAG strted.. ")
            chat_history=chat_history or []
            payload={'input':user_input,"chat_history":chat_history}
            answer=self.chain.invoke(payload)
            if not answer:
                self.log.warning("No answer generated",user_input=user_input,session_id=self.session_id)
                return "no answer available"
            self.log.info("Chain invoke successfully and answer generated",session_id=self.session_id,
                          user_input=user_input,answer_preview=answer[:150])
            return answer

        except Exception as e:
            self.log.error("Failed to invoke ConversationalRAG",error=str(e))
            raise DocumentPortalException("Failed to invoke ConversationalRAG",sys)
    def _load_llm(self):
        try:
            llm=ModelLoader().load_llm()
            if not llm:
                raise ValueError("LLM could not be loaded.")
            self.log.info("LLM loaded successfully",session_id=self.session_id)
            return llm
        except Exception as e:
            self.log.error("Failed to llm",error=str(e))
            raise DocumentPortalException("Failed to llm",sys)

    @staticmethod
    def _format_docs(docs):
        return "\n\n".join(d.page_content for d in docs)
            

    def _build_lcel_chain(self):
        try:
            self.log.info("Building LCEL chain started...")
            question_rewriter=(
                {
                    "input":itemgetter("input"),"chat_history":itemgetter("chat_history")
                }
                | self.contextualize_prompt
                | self.llm
                | StrOutputParser()
            )

            retrieve_docs=question_rewriter | self.retriever | self._format_docs
            self.chain=(
                {
                    "context": retrieve_docs,
                    "input": itemgetter('input'),
                    "chat_history": itemgetter("chat_history")
                }
                | self.qa_prompt
                | self.llm
                | StrOutputParser()
            )
            self.log.info("LCEL chain built successfully",session_id=self.session_id)
            #return self.chain


        except Exception as e:
            self.log.error("Failed to build lcel chain",error=str(e))
            raise DocumentPortalException("Failed to build lcel chain",sys)