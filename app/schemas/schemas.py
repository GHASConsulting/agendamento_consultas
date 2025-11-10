from datetime import datetime, date, time
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.database.models import StatusAgendamento


# ========================================
# Schemas de Paciente
# ========================================
class PacienteBase(BaseModel):
    nome: str
    telefone: str
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[datetime] = None


class PacienteCreate(PacienteBase):
    pass


class PacienteUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    cpf: Optional[str] = None
    data_nascimento: Optional[datetime] = None


class Paciente(PacienteBase):
    id: int
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Schemas de Especialidade
# ========================================
class EspecialidadeBase(BaseModel):
    nome: str
    descricao: Optional[str] = None


class EspecialidadeCreate(EspecialidadeBase):
    pass


class Especialidade(EspecialidadeBase):
    id: int
    ativa: bool
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Schemas de Médico
# ========================================
class MedicoBase(BaseModel):
    nome: str
    crm: str
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    especialidade_id: int


class MedicoCreate(MedicoBase):
    pass


class MedicoUpdate(BaseModel):
    nome: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[EmailStr] = None
    ativo: Optional[bool] = None


class Medico(MedicoBase):
    id: int
    ativo: bool
    especialidade: Optional[Especialidade] = None
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Schemas de Disponibilidade
# ========================================
class DisponibilidadeBase(BaseModel):
    medico_id: int
    dia_semana: int  # 0=Segunda, 6=Domingo
    hora_inicio: time
    hora_fim: time


class DisponibilidadeCreate(DisponibilidadeBase):
    pass


class Disponibilidade(DisponibilidadeBase):
    id: int
    ativa: bool
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Schemas de Agendamento
# ========================================
class AgendamentoBase(BaseModel):
    paciente_id: int
    medico_id: int
    data_hora: datetime
    duracao_minutos: Optional[int] = 30
    observacoes: Optional[str] = None


class AgendamentoCreate(AgendamentoBase):
    pass


class AgendamentoUpdate(BaseModel):
    data_hora: Optional[datetime] = None
    observacoes: Optional[str] = None
    status: Optional[StatusAgendamento] = None


class AgendamentoReagendar(BaseModel):
    nova_data_hora: datetime
    motivo: Optional[str] = None


class AgendamentoCancelar(BaseModel):
    motivo: str


class Agendamento(AgendamentoBase):
    id: int
    status: StatusAgendamento
    paciente: Optional[Paciente] = None
    medico: Optional[Medico] = None
    confirmado_em: Optional[datetime] = None
    cancelado_em: Optional[datetime] = None
    criado_em: datetime
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========================================
# Schemas de Disponibilidade de Horários
# ========================================
class HorarioDisponivel(BaseModel):
    """Schema para representar um horário disponível"""

    data_hora: datetime
    medico_id: int
    medico_nome: str
    especialidade: str


class DisponibilidadeConsulta(BaseModel):
    """Schema para consulta de disponibilidade"""

    medico_id: Optional[int] = None
    especialidade_id: Optional[int] = None
    data_inicio: date
    data_fim: date


class DisponibilidadeResponse(BaseModel):
    """Schema para resposta de disponibilidade"""

    horarios_disponiveis: list[HorarioDisponivel]
    total: int


# ========================================
# Schemas Botconversa
# ========================================
class BotconversaWebhook(BaseModel):
    """Schema para receber webhooks do Botconversa."""

    type: str
    contact: Optional[dict] = None
    message: Optional[dict] = None
    status: Optional[str] = None


class BotconversaMessage(BaseModel):
    """Schema para enviar mensagens via Botconversa."""

    phone: str
    message: str


class N8NWebhookData(BaseModel):
    """Schema para receber dados do N8N com respostas dos pacientes."""

    telefone: str
    subscriber_id: int
    resposta: str
    nome_paciente: Optional[str] = None
    mensagem_original: Optional[str] = None


# ========================================
# Schemas Botconversa - Fluxo de Agendamento
# ========================================
class EspecialidadeBotconversa(BaseModel):
    """Schema formatado para Botconversa - Especialidade"""

    id: int
    nome: str
    descricao: Optional[str] = None


class MedicoBotconversa(BaseModel):
    """Schema formatado para Botconversa - Médico"""

    id: int
    nome: str
    crm: str
    especialidade_nome: str


class DataDisponivelBotconversa(BaseModel):
    """Schema formatado para Botconversa - Data disponível"""

    data: date  # Formato: YYYY-MM-DD
    data_formatada: str  # Formato legível: "19/12/2024"
    dia_semana: str  # Ex: "Quinta-feira"


class HorarioDisponivelBotconversa(BaseModel):
    """Schema formatado para Botconversa - Horário disponível"""

    horario: str  # Formato: "HH:MM"
    data_hora: datetime  # Para uso interno na criação do agendamento


class EspecialidadesResponse(BaseModel):
    """Resposta com lista de especialidades para Botconversa"""

    especialidades: list[EspecialidadeBotconversa]
    total: int
    mensagem: Optional[str] = "Escolha uma especialidade:"


class MedicosResponse(BaseModel):
    """Resposta com lista de médicos para Botconversa"""

    medicos: list[MedicoBotconversa]
    total: int
    especialidade_nome: str
    mensagem: Optional[str] = "Escolha um médico:"


class DatasDisponiveisResponse(BaseModel):
    """Resposta com datas disponíveis para Botconversa"""

    datas: list[DataDisponivelBotconversa]
    total: int
    medico_nome: str
    mensagem: Optional[str] = "Escolha uma data:"


class HorariosDisponiveisResponse(BaseModel):
    """Resposta com horários disponíveis para Botconversa"""

    horarios: list[HorarioDisponivelBotconversa]
    total: int
    medico_nome: str
    data_formatada: str
    mensagem: Optional[str] = "Escolha um horário:"


class AgendamentoBotconversaCreate(BaseModel):
    """Schema para criar agendamento via Botconversa"""

    telefone: str  # Telefone do paciente (pode criar ou buscar existente)
    medico_id: int
    data_hora: datetime  # Data e hora escolhida
    duracao_minutos: Optional[int] = 30
    observacoes: Optional[str] = None
    nome_paciente: Optional[str] = None  # Se fornecido, atualiza ou cria paciente


class AgendamentoConfirmacaoResponse(BaseModel):
    """Resposta com mensagem de confirmação do agendamento"""

    agendamento_id: int
    mensagem: str
    agendamento: Agendamento  # Dados completos do agendamento criado
