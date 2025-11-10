import sys
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config.config import settings
from app.database.manager import create_tables, initialize_database

# Configuração de logs
logger.remove()
logger.add(sys.stdout, level=settings.log_level)
logger.add(
    "logs/app.log", rotation="1 day", retention="30 days", level=settings.log_level
)

# Criação da aplicação FastAPI
app = FastAPI(
    title=f"{settings.hospital_name or 'Hospital'} - Sistema de Agendamento de Consultas",
    description="API para agendamento de consultas médicas via WhatsApp com Botconversa",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configuração de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Inicialização do banco de dados
@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    try:
        logger.info("Inicializando aplicação...")

        # Inicializa o banco de dados
        initialize_database()
        logger.info("Banco de dados inicializado")

        # Cria as tabelas se não existirem
        create_tables()
        logger.info("Tabelas criadas/verificadas")

        logger.info("Aplicação inicializada com sucesso!")

    except Exception as e:
        logger.error(f"Erro na inicialização: {str(e)}")
        raise e


@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    logger.info("Encerrando aplicação...")


# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware para logging de requisições"""
    start_time = datetime.now()
    response = await call_next(request)
    process_time = (datetime.now() - start_time).total_seconds()

    logger.info(
        f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s"
    )

    return response


# Tratamento de exceções
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Erro interno do servidor"},
    )


@app.get("/")
async def root():
    """Endpoint raiz da aplicação"""
    hospital_name = settings.hospital_name or "Hospital"
    return {
        "message": f"Bem-vindo ao {hospital_name} - Sistema de Agendamento de Consultas",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
async def health_check():
    """Endpoint para verificação de saúde da aplicação"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
    }


# Inclusão dos routers
from app.api.routes import agendamento, paciente, medico, disponibilidade, botconversa

app.include_router(agendamento.router, prefix="/api/v1", tags=["agendamentos"])
app.include_router(paciente.router, prefix="/api/v1", tags=["pacientes"])
app.include_router(medico.router, prefix="/api/v1", tags=["medicos"])
app.include_router(disponibilidade.router, prefix="/api/v1", tags=["disponibilidade"])
app.include_router(botconversa.router, prefix="/api/v1", tags=["botconversa"])


if __name__ == "__main__":
    import uvicorn

    host = getattr(settings, "webhook_host", "0.0.0.0")
    port = getattr(settings, "webhook_port", 8000)

    logger.info(f"Iniciando servidor em {host}:{port}")

    uvicorn.run(
        "app.main:app",
        host=host,
        port=port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

