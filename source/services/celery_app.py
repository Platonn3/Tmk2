from celery import Celery


celery_app = Celery(
    'articles',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0',
    include=['source.services.llm']
)