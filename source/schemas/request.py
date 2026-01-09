from pydantic import HttpUrl, BaseModel


class ArticleDownload(BaseModel):
    url: HttpUrl