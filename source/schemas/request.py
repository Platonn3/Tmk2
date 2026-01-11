from pydantic import HttpUrl, BaseModel


class ArticleDownload(BaseModel):
    url: HttpUrl

class HypothesisRequest(BaseModel):
    text: str