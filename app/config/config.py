from enum import Enum

from pydantic_settings import BaseSettings


class DataBaseType(str, Enum):
    """Tipos de banco de dados suportados pela aplicação."""

    SQLITE = "sqlite"
    ORACLE = "oracle"
    POSTGRESQL = "postgresql"
    FIREBIRD = "firebird"


class Settings(BaseSettings):
    """
    Configurações da aplicação carregadas de variáveis de ambiente.

    Suporta múltiplos tipos de banco de dados (SQLite, Oracle, PostgreSQL, Firebird)
    e configurações para APIs externas (Botconversa).
    """

    # Database Configuration
    database_type: DataBaseType = DataBaseType.SQLITE
    database_url: str | None = None

    # SQLite specific configuration
    sqlite_url: str = "sqlite:///./agendamento_consultas.db"

    # Oracle specific configuration
    oracle_url: str | None = None

    # PostgreSQL specific configuration
    postgresql_url: str | None = None

    # Firebird specific configuration
    firebird_url: str | None = None

    # Botconversa API Configuration
    botconversa_api_url: str = "https://backend.botconversa.com.br/api/v1/webhook"
    botconversa_webhook_secret: str | None = None
    botconversa_api_key: str | None = None

    # Application Configuration
    app_secret_key: str | None = None
    hospital_name: str | None = None
    debug: bool = False
    log_level: str = "INFO"

    # Hospital Information
    hospital_phone: str | None = None
    hospital_address: str | None = None
    hospital_city: str | None = None
    hospital_state: str | None = None

    # Performance settings Configuration
    max_workers: int = 4
    worker_timeout: int = 30

    # Webhook Configuration
    webhook_host: str = "0.0.0.0"
    webhook_port: int = 8000
    webhook_url: str | None = None

    # Scheduler Configuration
    reminder_interval: int = 24
    confirmation_window_hours: int = 72

    # Scheduler Time Configuration
    scheduler_confirmation_hour: int = 9
    scheduler_confirmation_minute: int = 0
    scheduler_reminder_hour: int = 14
    scheduler_reminder_minute: int = 0

    # Scheduler Job Configuration
    scheduler_enable_confirmation_job: bool = True
    scheduler_enable_reminder_job: bool = True

    # Agendamento Configuration
    min_advance_booking_hours: int = 24
    max_advance_booking_days: int = 90
    default_consultation_duration_minutes: int = 30
    consultation_interval_minutes: int = 30

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"

    @property
    def get_database_url(self) -> str:
        """
        Retorna a URL do banco de dados baseado no tipo selecionado.

        Returns:
            str: URL do banco de dados configurado

        Raises:
            ValueError: Se o tipo de banco de dados não for suportado
        """
        if self.database_type == DataBaseType.SQLITE:
            return self.database_url or self.sqlite_url
        elif self.database_type == DataBaseType.ORACLE:
            return self.oracle_url or self.database_url or ""
        elif self.database_type == DataBaseType.POSTGRESQL:
            return self.postgresql_url or self.database_url or ""
        elif self.database_type == DataBaseType.FIREBIRD:
            return self.firebird_url or self.database_url or ""
        else:
            raise ValueError(
                f"Tipo de banco de dados não suportado: {self.database_type}"
            )


settings = Settings()

