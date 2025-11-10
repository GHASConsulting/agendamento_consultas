from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from loguru import logger

from app.config.config import settings, DataBaseType
from app.database.base import Base

# Importa os modelos para que sejam registrados no Base.metadata
from app.database.models import (
    Paciente,
    Medico,
    Especialidade,
    Disponibilidade,
    Agendamento,
    StatusAgendamento,
)

# Variáveis globais para diferentes tipos de banco
engine = None
SessionLocal = None


class DatabaseManager:
    """Gerenciador de conexões com diferentes bancos de dados"""

    def __init__(self):
        self.database_type = settings.database_type
        self.engine = None
        self.session_local = None

    def _initialize_sqlite(self):
        """Inicializa conexão com SQLite"""
        try:
            database_url = settings.get_database_url
            if not database_url:
                raise ValueError("SQLite URL não configurada")

            # SQLite não precisa de pool, mas precisamos de check_same_thread=False para FastAPI
            self.engine = create_engine(
                database_url,
                connect_args={"check_same_thread": False},
                echo=settings.debug
            )
            self.session_local = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info(f"Conexão com SQLite inicializada com sucesso: {database_url}")

        except Exception as e:
            logger.error(f"Erro ao inicializar SQLite: {str(e)}")
            raise

    def initialize_database(self):
        """Inicializa a conexão com o banco de dados baseado no tipo configurado"""
        if self.database_type == DataBaseType.SQLITE:
            self._initialize_sqlite()
        elif self.database_type == DataBaseType.ORACLE:
            self._initialize_oracle()
        elif self.database_type == DataBaseType.POSTGRESQL:
            self._initialize_postgresql()
        elif self.database_type == DataBaseType.FIREBIRD:
            self._initialize_firebird()
        else:
            raise ValueError(
                f"Tipo de banco de dados não suportado: {self.database_type}"
            )

    def _initialize_oracle(self):
        """Inicializa conexão com Oracle"""
        try:
            database_url = settings.get_database_url
            if not database_url:
                raise ValueError("Oracle URL não configurada")

            self.engine = create_engine(
                database_url, pool_pre_ping=True, pool_recycle=3600, echo=settings.debug
            )
            self.session_local = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info("Conexão com Oracle inicializada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar Oracle: {str(e)}")
            raise

    def _initialize_postgresql(self):
        """Inicializa conexão com PostgreSQL"""
        try:
            database_url = settings.get_database_url
            if not database_url:
                raise ValueError("PostgreSQL URL não configurada")

            self.engine = create_engine(
                database_url, pool_pre_ping=True, pool_recycle=3600, echo=settings.debug
            )
            self.session_local = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info("Conexão com PostgreSQL inicializada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar PostgreSQL: {str(e)}")
            raise

    def _initialize_firebird(self):
        """Inicializa conexão com Firebird"""
        try:
            database_url = settings.get_database_url
            if not database_url:
                raise ValueError("Firebird URL não configurada")

            self.engine = create_engine(
                database_url, pool_pre_ping=True, pool_recycle=3600, echo=settings.debug
            )
            self.session_local = sessionmaker(
                autocommit=False, autoflush=False, bind=self.engine
            )
            logger.info("Conexão com Firebird inicializada com sucesso")

        except Exception as e:
            logger.error(f"Erro ao inicializar Firebird: {str(e)}")
            raise

    def get_session(self):
        """Retorna uma sessão do banco de dados"""
        if self.database_type in [
            DataBaseType.SQLITE,
            DataBaseType.ORACLE,
            DataBaseType.POSTGRESQL,
            DataBaseType.FIREBIRD,
        ]:
            if not self.session_local:
                raise RuntimeError("Sessão não inicializada")
            return self.session_local()
        else:
            raise ValueError(
                f"Tipo de banco de dados não suportado: {self.database_type}"
            )

    def create_tables(self):
        """Cria as tabelas no banco de dados"""
        if self.database_type in [
            DataBaseType.SQLITE,
            DataBaseType.ORACLE,
            DataBaseType.POSTGRESQL,
            DataBaseType.FIREBIRD,
        ]:
            if self.engine:
                Base.metadata.create_all(bind=self.engine)
                logger.info("Tabelas criadas com sucesso")
        else:
            raise ValueError(
                f"Tipo de banco de dados não suportado: {self.database_type}"
            )


# Instância global do gerenciador de banco
db_manager = DatabaseManager()


def initialize_database():
    """Inicializa o banco de dados globalmente"""
    global engine, SessionLocal

    db_manager.initialize_database()

    if db_manager.database_type in [
        DataBaseType.SQLITE,
        DataBaseType.ORACLE,
        DataBaseType.POSTGRESQL,
        DataBaseType.FIREBIRD,
    ]:
        engine = db_manager.engine
        SessionLocal = db_manager.session_local


def get_db():
    """Dependency para FastAPI - retorna sessão do banco"""
    if settings.database_type in [
        DataBaseType.SQLITE,
        DataBaseType.ORACLE,
        DataBaseType.POSTGRESQL,
        DataBaseType.FIREBIRD,
    ]:
        if not SessionLocal:
            raise RuntimeError("Banco de dados não inicializado")

        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    else:
        raise ValueError(
            f"Tipo de banco de dados não suportado: {settings.database_type}"
        )


def create_tables():
    """Cria as tabelas no banco de dados"""
    db_manager.create_tables()

