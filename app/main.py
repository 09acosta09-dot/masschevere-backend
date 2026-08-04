from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import usuarios
from app.routes import auth
from app.routes import ordenes
from app.routes import comprobantes

app = FastAPI(
    title="MassChevere API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://masschevere.com",
        "https://www.masschevere.com",
        "http://127.0.0.1:5500",
        "http://localhost:5500"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(usuarios.router)
app.include_router(auth.router)
app.include_router(ordenes.router)
app.include_router(comprobantes.router)


@app.get("/")
def inicio():
    return {"mensaje": "Backend funcionando"}