from pydantic import BaseModel,Field
from typing import Optional,Dict,List,Any,Union

class Metadata(BaseModel):
    Summary: List[str]= Field(default_factory=list,description="Summary of the document.")
    Title: str
    Author: str
    DateCreated: str
    LastModifiedDate: str
    Publisher: str
    Language: str
    PageCount: Union[int, str]
    SentimentTone: str