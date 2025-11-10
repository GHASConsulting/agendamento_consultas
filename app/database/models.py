import enum
from datetime import time

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class StatusAgendamento(enum.Enum):
    """
    Enumeração dos possíveis status de agendamento.

    Attributes:
        AGENDADO: Consulta agendada, aguardando confirmação
        CONFIRMADO: Consulta confirmada pelo paciente
        CANCELADO: Consulta cancelada
        REAGENDADO: Consulta reagendada
        CONCLUIDA: Consulta realizada
        FALTA: Paciente faltou à consulta
    """

    AGENDADO = "agendado"
    CONFIRMADO = "confirmado"
    CANCELADO = "cancelado"
    REAGENDADO = "reagendado"
    CONCLUIDA = "concluida"
    FALTA = "falta"


class Paciente(Base):
    """
    Modelo para representar um paciente no sistema.

    Attributes:
        id: Identificador único do paciente
        nome: Nome completo do paciente
        telefone: Número de telefone (único)
        email: Endereço de email do paciente
        cpf: CPF do paciente (opcional)
        data_nascimento: Data de nascimento (opcional)
        criado_em: Data/hora de criação do registro
        atualizado_em: Data/hora da última atualização
        agendamentos: Relacionamento com os agendamentos do paciente
    """

    __tablename__ = "pacientes"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    telefone = Column(String(20), unique=True, nullable=False, index=True)
    email = Column(String(255))
    cpf = Column(String(14), unique=True, nullable=True, index=True)
    data_nascimento = Column(DateTime(timezone=True), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    agendamentos = relationship("Agendamento", back_populates="paciente")


class Especialidade(Base):
    """
    Modelo para representar especialidades médicas.

    Attributes:
        id: Identificador único da especialidade
        nome: Nome da especialidade (ex: Cardiologia, Pediatria)
        descricao: Descrição da especialidade
        ativa: Indica se a especialidade está ativa
        criado_em: Data/hora de criação do registro
        atualizado_em: Data/hora da última atualização
        medicos: Relacionamento com os médicos desta especialidade
    """

    __tablename__ = "especialidades"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False, unique=True, index=True)
    descricao = Column(Text)
    ativa = Column(Boolean, default=True, nullable=False)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    medicos = relationship("Medico", back_populates="especialidade")


class Medico(Base):
    """
    Modelo para representar um médico no sistema.

    Attributes:
        id: Identificador único do médico
        nome: Nome completo do médico
        crm: CRM do médico (único)
        telefone: Telefone de contato
        email: Email do médico
        especialidade_id: ID da especialidade (chave estrangeira)
        ativo: Indica se o médico está ativo
        criado_em: Data/hora de criação do registro
        atualizado_em: Data/hora da última atualização
        especialidade: Relacionamento com a especialidade
        disponibilidades: Relacionamento com as disponibilidades do médico
        agendamentos: Relacionamento com os agendamentos do médico
    """

    __tablename__ = "medicos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    crm = Column(String(20), unique=True, nullable=False, index=True)
    telefone = Column(String(20))
    email = Column(String(255))
    especialidade_id = Column(Integer, ForeignKey("especialidades.id"), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    especialidade = relationship("Especialidade", back_populates="medicos")
    disponibilidades = relationship("Disponibilidade", back_populates="medico")
    agendamentos = relationship("Agendamento", back_populates="medico")


class Disponibilidade(Base):
    """
    Modelo para representar disponibilidade de horários de um médico.

    Define os horários em que um médico está disponível para atendimento.

    Attributes:
        id: Identificador único da disponibilidade
        medico_id: ID do médico (chave estrangeira)
        dia_semana: Dia da semana (0=Segunda, 6=Domingo)
        hora_inicio: Hora de início do atendimento
        hora_fim: Hora de fim do atendimento
        ativa: Indica se a disponibilidade está ativa
        criado_em: Data/hora de criação do registro
        atualizado_em: Data/hora da última atualização
        medico: Relacionamento com o médico
    """

    __tablename__ = "disponibilidades"

    id = Column(Integer, primary_key=True, index=True)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    dia_semana = Column(Integer, nullable=False)  # 0=Segunda, 6=Domingo
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=False)
    ativa = Column(Boolean, default=True, nullable=False)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    medico = relationship("Medico", back_populates="disponibilidades")


class Agendamento(Base):
    """
    Modelo para representar um agendamento de consulta médica.

    Attributes:
        id: Identificador único do agendamento
        paciente_id: ID do paciente (chave estrangeira)
        medico_id: ID do médico (chave estrangeira)
        data_hora: Data e hora do agendamento
        duracao_minutos: Duração da consulta em minutos
        status: Status atual do agendamento
        observacoes: Observações adicionais
        subscriber_id: ID do subscriber no Botconversa
        mensagem_enviada: Mensagem enviada ao paciente
        resposta_paciente: Resposta recebida do paciente
        confirmado_em: Data/hora da confirmação
        cancelado_em: Data/hora do cancelamento
        motivo_cancelamento: Motivo do cancelamento
        criado_em: Data/hora de criação do registro
        atualizado_em: Data/hora da última atualização
        paciente: Relacionamento com o paciente
        medico: Relacionamento com o médico
    """

    __tablename__ = "agendamentos"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("pacientes.id"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medicos.id"), nullable=False)
    data_hora = Column(DateTime, nullable=False, index=True)
    duracao_minutos = Column(Integer, default=30, nullable=False)
    status = Column(
        Enum(StatusAgendamento), default=StatusAgendamento.AGENDADO, nullable=False
    )

    observacoes = Column(Text)
    subscriber_id = Column(Integer, unique=True, nullable=True, index=True)

    # Dados de mensagem e resposta (Botconversa)
    mensagem_enviada = Column(Text)
    resposta_paciente = Column(Text)
    interpretacao_resposta = Column(String(50))

    # Controle de lembretes
    lembrete_48h_enviado = Column(Boolean, default=False)
    lembrete_12h_enviado = Column(Boolean, default=False)
    ultimo_lembrete_enviado = Column(DateTime(timezone=True))
    tipo_ultimo_lembrete = Column(String(10))

    # Timestamps importantes
    confirmado_em = Column(DateTime(timezone=True))
    cancelado_em = Column(DateTime(timezone=True))
    motivo_cancelamento = Column(Text)
    enviado_em = Column(DateTime(timezone=True))
    respondido_em = Column(DateTime(timezone=True))

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    paciente = relationship("Paciente", back_populates="agendamentos")
    medico = relationship("Medico", back_populates="agendamentos")

