from fastapi import FastAPI
from fastapi import APIRouter
from app.api.v1.routes.todo import router as todo_router
from app.core.database import engine
from app.models.todo import SQLModel
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    servers=[
        {"url": "http://localhost:8000", "description": "Local development server"},
    ]
)
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # List of allowed origins
    allow_credentials=True,  # Allow cookies and credentials
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Create the database tables
@app.on_event("startup")
def on_startup():
    SQLModel.metadata.create_all(engine)

# Include routes
app.include_router(todo_router, prefix="/api/v1/todo")
