"""
Serviço para gestão de agendamentos.

Este serviço gerencia:
- CRUD de agendamentos
- Validação de disponibilidade
- Verificação de conflitos de horário
- Reagendamento e cancelamento
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date
from loguru import logger
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError

from app.database.models import (
    Agendamento,
    Medico,
    Disponibilidade,
    StatusAgendamento,
)
from app.config.config import settings


class AgendamentoService:
    """Serviço para gestão de agendamentos"""

    def __init__(self, db: Session):
        self.db = db

    def criar_agendamento(self, dados: Dict[str, Any]) -> Optional[Agendamento]:
        """
        Cria um novo agendamento.
        
        Args:
            dados: Dicionário com dados do agendamento (paciente_id, medico_id, data_hora, etc.)
            
        Returns:
            Agendamento criado ou None em caso de erro
        """
        paciente_id = dados.get("paciente_id")
        medico_id = dados.get("medico_id")
        data_hora = dados.get("data_hora")
        duracao_minutos = dados.get("duracao_minutos", 30)
        
        logger.info(
            f"Iniciando criação de agendamento | paciente_id={paciente_id} | "
            f"medico_id={medico_id} | data_hora={data_hora} | duracao={duracao_minutos}min"
        )
        
        try:
            # Valida disponibilidade
            logger.debug(f"Validando disponibilidade para médico {medico_id} em {data_hora}")
            if not self._validar_disponibilidade(medico_id, data_hora, duracao_minutos):
                logger.warning(
                    f"Validação de disponibilidade falhou | paciente_id={paciente_id} | "
                    f"medico_id={medico_id} | data_hora={data_hora}"
                )
                return None

            logger.debug("Disponibilidade validada com sucesso, criando agendamento")
            
            # Cria agendamento
            agendamento = Agendamento(
                paciente_id=paciente_id,
                medico_id=medico_id,
                data_hora=data_hora,
                duracao_minutos=duracao_minutos,
                observacoes=dados.get("observacoes"),
                status=StatusAgendamento.AGENDADO,
            )

            self.db.add(agendamento)
            
            try:
                self.db.commit()
                self.db.refresh(agendamento)
                
                # Revalida após commit para detectar race conditions
                # (caso outro agendamento tenha sido criado entre a validação e o commit)
                if not self._validar_disponibilidade(medico_id, data_hora, duracao_minutos, excluir_agendamento_id=agendamento.id):
                    # Se após criar ainda há conflito, significa que criamos um duplicado
                    logger.warning(
                        f"Conflito detectado após criação - possível race condition | "
                        f"agendamento_id={agendamento.id} | medico_id={medico_id} | data_hora={data_hora}"
                    )
                    # Remove o agendamento duplicado
                    self.db.delete(agendamento)
                    self.db.commit()
                    return None

                logger.success(
                    f"Agendamento criado com sucesso | agendamento_id={agendamento.id} | "
                    f"paciente_id={paciente_id} | medico_id={medico_id} | "
                    f"data_hora={data_hora} | status={agendamento.status.value}"
                )
                return agendamento
                
            except IntegrityError as e:
                # Erro de constraint única (Oracle/PostgreSQL) - horário já ocupado
                self.db.rollback()
                logger.warning(
                    f"Conflito de integridade detectado - horário já ocupado | "
                    f"medico_id={medico_id} | data_hora={data_hora} | erro={str(e)}"
                )
                # Revalida para confirmar que realmente está ocupado
                if not self._validar_disponibilidade(medico_id, data_hora, duracao_minutos):
                    logger.info(
                        f"Confirmação: horário realmente está ocupado | "
                        f"medico_id={medico_id} | data_hora={data_hora}"
                    )
                return None

        except KeyError as e:
            logger.error(
                f"Campo obrigatório ausente ao criar agendamento | campo={str(e)} | "
                f"dados_recebidos={list(dados.keys())}"
            )
            self.db.rollback()
            return None
        except Exception as e:
            logger.exception(
                f"Erro inesperado ao criar agendamento | paciente_id={paciente_id} | "
                f"medico_id={medico_id} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def buscar_agendamento(self, agendamento_id: int) -> Optional[Agendamento]:
        """
        Busca um agendamento por ID.
        
        Args:
            agendamento_id: ID do agendamento a ser buscado
            
        Returns:
            Agendamento encontrado ou None
        """
        logger.debug(f"Buscando agendamento | agendamento_id={agendamento_id}")
        
        try:
            agendamento = (
                self.db.query(Agendamento)
                .filter(Agendamento.id == agendamento_id)
                .first()
            )
            
            if agendamento:
                logger.debug(
                    f"Agendamento encontrado | agendamento_id={agendamento_id} | "
                    f"paciente_id={agendamento.paciente_id} | medico_id={agendamento.medico_id} | "
                    f"status={agendamento.status.value}"
                )
            else:
                logger.warning(f"Agendamento não encontrado | agendamento_id={agendamento_id}")
            
            return agendamento
            
        except Exception as e:
            logger.exception(
                f"Erro ao buscar agendamento | agendamento_id={agendamento_id} | erro={str(e)}"
            )
            return None

    def listar_agendamentos(
        self,
        skip: int = 0,
        limit: int = 100,
        medico_id: Optional[int] = None,
        paciente_id: Optional[int] = None,
        status: Optional[StatusAgendamento] = None,
    ) -> List[Agendamento]:
        """
        Lista agendamentos com filtros opcionais.
        
        Args:
            skip: Número de registros para pular (paginação)
            limit: Número máximo de registros a retornar
            medico_id: Filtrar por médico específico
            paciente_id: Filtrar por paciente específico
            status: Filtrar por status específico
            
        Returns:
            Lista de agendamentos encontrados
        """
        logger.debug(
            f"Listando agendamentos | skip={skip} | limit={limit} | "
            f"medico_id={medico_id} | paciente_id={paciente_id} | status={status.value if status else None}"
        )
        
        try:
            query = self.db.query(Agendamento)

            if medico_id:
                query = query.filter(Agendamento.medico_id == medico_id)
            if paciente_id:
                query = query.filter(Agendamento.paciente_id == paciente_id)
            if status:
                query = query.filter(Agendamento.status == status)

            agendamentos = query.order_by(Agendamento.data_hora.asc()).offset(skip).limit(limit).all()
            
            logger.info(
                f"Agendamentos listados com sucesso | total_encontrado={len(agendamentos)} | "
                f"filtros_aplicados=medico_id:{medico_id}, paciente_id:{paciente_id}, status:{status.value if status else None}"
            )
            
            return agendamentos
            
        except Exception as e:
            logger.exception(
                f"Erro ao listar agendamentos | skip={skip} | limit={limit} | erro={str(e)}"
            )
            return []

    def _validar_disponibilidade(
        self, medico_id: int, data_hora: datetime, duracao_minutos: int, excluir_agendamento_id: Optional[int] = None
    ) -> bool:
        """
        Valida se um horário está disponível para agendamento.
        
        Validações realizadas:
        - Médico existe e está ativo
        - Data/hora não é no passado
        - Respeita antecedência mínima e máxima
        - Médico atende no dia da semana
        - Horário está dentro do período de disponibilidade
        - Não há conflitos com outros agendamentos
        
        Args:
            medico_id: ID do médico
            data_hora: Data e hora do agendamento
            duracao_minutos: Duração da consulta em minutos
            
        Returns:
            True se disponível, False caso contrário
        """
        logger.debug(
            f"Iniciando validação de disponibilidade | medico_id={medico_id} | "
            f"data_hora={data_hora} | duracao={duracao_minutos}min"
        )
        
        try:
            # Verifica se o médico existe e está ativo
            medico = self.db.query(Medico).filter(Medico.id == medico_id).first()
            if not medico:
                logger.warning(f"Médico não encontrado | medico_id={medico_id}")
                return False
            if not medico.ativo:
                logger.warning(
                    f"Médico inativo | medico_id={medico_id} | nome={medico.nome}"
                )
                return False

            logger.debug(f"Médico validado | medico_id={medico_id} | nome={medico.nome}")

            # Verifica se a data é no futuro
            agora = datetime.now()
            if data_hora < agora:
                logger.warning(
                    f"Tentativa de agendar em data passada | medico_id={medico_id} | "
                    f"data_hora={data_hora} | agora={agora}"
                )
                return False

            # Verifica antecedência mínima
            min_advance = timedelta(hours=settings.min_advance_booking_hours)
            data_minima = agora + min_advance
            if data_hora < data_minima:
                logger.warning(
                    f"Antecedência mínima não respeitada | medico_id={medico_id} | "
                    f"data_hora={data_hora} | data_minima={data_minima} | "
                    f"horas_minimas={settings.min_advance_booking_hours}"
                )
                return False

            # Verifica antecedência máxima
            max_advance = timedelta(days=settings.max_advance_booking_days)
            data_maxima = agora + max_advance
            if data_hora > data_maxima:
                logger.warning(
                    f"Antecedência máxima excedida | medico_id={medico_id} | "
                    f"data_hora={data_hora} | data_maxima={data_maxima} | "
                    f"dias_maximos={settings.max_advance_booking_days}"
                )
                return False

            # Verifica disponibilidade do médico no dia da semana
            dia_semana = data_hora.weekday()
            disponibilidade = (
                self.db.query(Disponibilidade)
                .filter(
                    and_(
                        Disponibilidade.medico_id == medico_id,
                        Disponibilidade.dia_semana == dia_semana,
                        Disponibilidade.ativa == True,
                    )
                )
                .first()
            )

            if not disponibilidade:
                logger.warning(
                    f"Médico não atende neste dia da semana | medico_id={medico_id} | "
                    f"dia_semana={dia_semana} | data_hora={data_hora}"
                )
                return False

            logger.debug(
                f"Disponibilidade encontrada | medico_id={medico_id} | "
                f"dia_semana={dia_semana} | hora_inicio={disponibilidade.hora_inicio} | "
                f"hora_fim={disponibilidade.hora_fim}"
            )

            # Verifica se o horário está dentro do período de disponibilidade
            hora_consulta = data_hora.time()
            if (
                hora_consulta < disponibilidade.hora_inicio
                or hora_consulta >= disponibilidade.hora_fim
            ):
                logger.warning(
                    f"Horário fora do período de disponibilidade | medico_id={medico_id} | "
                    f"hora_consulta={hora_consulta} | hora_inicio={disponibilidade.hora_inicio} | "
                    f"hora_fim={disponibilidade.hora_fim}"
                )
                return False

            # Verifica conflitos com outros agendamentos
            fim_consulta = data_hora + timedelta(minutes=duracao_minutos)
            
            # Busca agendamentos que podem conflitar
            filtros = [
                Agendamento.medico_id == medico_id,
                Agendamento.status.in_(
                    [
                        StatusAgendamento.AGENDADO,
                        StatusAgendamento.CONFIRMADO,
                    ]
                ),
                Agendamento.data_hora < fim_consulta,
            ]
            
            # Exclui um agendamento específico da validação (útil para revalidação após criação)
            if excluir_agendamento_id is not None:
                filtros.append(Agendamento.id != excluir_agendamento_id)
            
            agendamentos_existentes = (
                self.db.query(Agendamento)
                .filter(and_(*filtros))
                .all()
            )
            
            # Verifica conflitos manualmente para cada agendamento
            conflitos = None
            for agendamento in agendamentos_existentes:
                fim_agendamento = agendamento.data_hora + timedelta(
                    minutes=agendamento.duracao_minutos
                )
                # Verifica se há sobreposição de horários
                if (
                    (agendamento.data_hora <= data_hora < fim_agendamento)
                    or (agendamento.data_hora < fim_consulta <= fim_agendamento)
                    or (data_hora <= agendamento.data_hora < fim_consulta)
                ):
                    conflitos = agendamento
                    break

            if conflitos:
                logger.warning(
                    f"Conflito de horário detectado | medico_id={medico_id} | "
                    f"data_hora={data_hora} | conflito_com_agendamento_id={conflitos.id} | "
                    f"conflito_data_hora={conflitos.data_hora}"
                )
                return False

            logger.debug(
                f"Validação de disponibilidade concluída com sucesso | medico_id={medico_id} | "
                f"data_hora={data_hora}"
            )
            return True

        except Exception as e:
            logger.exception(
                f"Erro ao validar disponibilidade | medico_id={medico_id} | "
                f"data_hora={data_hora} | erro={str(e)}"
            )
            return False

    def reagendar(
        self, agendamento_id: int, nova_data_hora: datetime, motivo: Optional[str] = None
    ) -> Optional[Agendamento]:
        """
        Reagenda um agendamento para uma nova data/hora.
        
        Args:
            agendamento_id: ID do agendamento a ser reagendado
            nova_data_hora: Nova data e hora para o agendamento
            motivo: Motivo do reagendamento (opcional)
            
        Returns:
            Agendamento reagendado ou None em caso de erro
        """
        logger.info(
            f"Iniciando reagendamento | agendamento_id={agendamento_id} | "
            f"nova_data_hora={nova_data_hora} | motivo={motivo or 'Não informado'}"
        )
        
        try:
            agendamento = self.buscar_agendamento(agendamento_id)
            if not agendamento:
                logger.warning(f"Agendamento não encontrado para reagendamento | agendamento_id={agendamento_id}")
                return None

            data_hora_anterior = agendamento.data_hora
            logger.debug(
                f"Agendamento encontrado | agendamento_id={agendamento_id} | "
                f"data_hora_anterior={data_hora_anterior} | medico_id={agendamento.medico_id}"
            )

            # Valida nova disponibilidade
            logger.debug(f"Validando nova disponibilidade para reagendamento | medico_id={agendamento.medico_id}")
            if not self._validar_disponibilidade(
                agendamento.medico_id, nova_data_hora, agendamento.duracao_minutos
            ):
                logger.warning(
                    f"Nova data/hora não está disponível para reagendamento | agendamento_id={agendamento_id} | "
                    f"nova_data_hora={nova_data_hora} | medico_id={agendamento.medico_id}"
                )
                return None

            # Atualiza agendamento
            agendamento.data_hora = nova_data_hora
            agendamento.status = StatusAgendamento.REAGENDADO
            if motivo:
                agendamento.observacoes = (
                    f"{agendamento.observacoes or ''}\nReagendado: {motivo}"
                )
            agendamento.atualizado_em = datetime.now()

            self.db.commit()
            self.db.refresh(agendamento)

            logger.success(
                f"Agendamento reagendado com sucesso | agendamento_id={agendamento_id} | "
                f"data_hora_anterior={data_hora_anterior} | nova_data_hora={nova_data_hora} | "
                f"status={agendamento.status.value}"
            )
            return agendamento

        except Exception as e:
            logger.exception(
                f"Erro ao reagendar agendamento | agendamento_id={agendamento_id} | "
                f"nova_data_hora={nova_data_hora} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def cancelar(
        self, agendamento_id: int, motivo: str
    ) -> Optional[Agendamento]:
        """
        Cancela um agendamento.
        
        Args:
            agendamento_id: ID do agendamento a ser cancelado
            motivo: Motivo do cancelamento
            
        Returns:
            Agendamento cancelado ou None em caso de erro
        """
        logger.info(
            f"Iniciando cancelamento de agendamento | agendamento_id={agendamento_id} | "
            f"motivo={motivo[:50]}..."  # Limita tamanho do motivo no log
        )
        
        try:
            agendamento = self.buscar_agendamento(agendamento_id)
            if not agendamento:
                logger.warning(f"Agendamento não encontrado para cancelamento | agendamento_id={agendamento_id}")
                return None

            status_anterior = agendamento.status
            logger.debug(
                f"Agendamento encontrado | agendamento_id={agendamento_id} | "
                f"status_anterior={status_anterior.value} | paciente_id={agendamento.paciente_id} | "
                f"medico_id={agendamento.medico_id} | data_hora={agendamento.data_hora}"
            )

            agendamento.status = StatusAgendamento.CANCELADO
            agendamento.motivo_cancelamento = motivo
            agendamento.cancelado_em = datetime.now()
            agendamento.atualizado_em = datetime.now()

            self.db.commit()
            self.db.refresh(agendamento)

            logger.success(
                f"Agendamento cancelado com sucesso | agendamento_id={agendamento_id} | "
                f"status_anterior={status_anterior.value} | status_novo={agendamento.status.value} | "
                f"paciente_id={agendamento.paciente_id}"
            )
            return agendamento

        except Exception as e:
            logger.exception(
                f"Erro ao cancelar agendamento | agendamento_id={agendamento_id} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def confirmar(self, agendamento_id: int) -> Optional[Agendamento]:
        """
        Confirma um agendamento.
        
        Args:
            agendamento_id: ID do agendamento a ser confirmado
            
        Returns:
            Agendamento confirmado ou None em caso de erro
        """
        logger.info(f"Iniciando confirmação de agendamento | agendamento_id={agendamento_id}")
        
        try:
            agendamento = self.buscar_agendamento(agendamento_id)
            if not agendamento:
                logger.warning(f"Agendamento não encontrado para confirmação | agendamento_id={agendamento_id}")
                return None

            status_anterior = agendamento.status
            logger.debug(
                f"Agendamento encontrado | agendamento_id={agendamento_id} | "
                f"status_anterior={status_anterior.value} | paciente_id={agendamento.paciente_id} | "
                f"medico_id={agendamento.medico_id} | data_hora={agendamento.data_hora}"
            )

            agendamento.status = StatusAgendamento.CONFIRMADO
            agendamento.confirmado_em = datetime.now()
            agendamento.atualizado_em = datetime.now()

            self.db.commit()
            self.db.refresh(agendamento)

            logger.success(
                f"Agendamento confirmado com sucesso | agendamento_id={agendamento_id} | "
                f"status_anterior={status_anterior.value} | status_novo={agendamento.status.value} | "
                f"paciente_id={agendamento.paciente_id} | confirmado_em={agendamento.confirmado_em}"
            )
            return agendamento

        except Exception as e:
            logger.exception(
                f"Erro ao confirmar agendamento | agendamento_id={agendamento_id} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def buscar_horarios_disponiveis(
        self,
        medico_id: Optional[int] = None,
        especialidade_id: Optional[int] = None,
        data_inicio: datetime = None,
        data_fim: datetime = None,
    ) -> List[Dict[str, Any]]:
        """
        Busca horários disponíveis para agendamento.
        
        Gera uma lista de horários disponíveis baseado nos filtros fornecidos,
        respeitando disponibilidades dos médicos e agendamentos existentes.
        
        Args:
            medico_id: Filtrar por médico específico
            especialidade_id: Filtrar por especialidade
            data_inicio: Data inicial da busca (padrão: agora)
            data_fim: Data final da busca (padrão: 30 dias à frente)
            
        Returns:
            Lista de dicionários com horários disponíveis
        """
        logger.debug(
            f"Iniciando busca de horários disponíveis | medico_id={medico_id} | "
            f"especialidade_id={especialidade_id} | data_inicio={data_inicio} | data_fim={data_fim}"
        )
        
        try:
            from app.database.models import Medico, Especialidade

            horarios_disponiveis = []

            # Define período padrão se não fornecido
            if not data_inicio:
                data_inicio = datetime.now()
            if not data_fim:
                data_fim = data_inicio + timedelta(days=30)

            logger.debug(
                f"Período de busca definido | data_inicio={data_inicio} | data_fim={data_fim} | "
                f"dias={(data_fim - data_inicio).days}"
            )

            # Busca médicos baseado nos filtros
            query = self.db.query(Medico).filter(Medico.ativo == True)

            if medico_id:
                query = query.filter(Medico.id == medico_id)
            if especialidade_id:
                query = query.filter(Medico.especialidade_id == especialidade_id)

            medicos = query.all()
            logger.debug(f"Médicos encontrados para busca de horários | total={len(medicos)}")

            for medico in medicos:
                logger.debug(f"Processando médico | medico_id={medico.id} | nome={medico.nome}")
                
                # Busca disponibilidades do médico
                disponibilidades = (
                    self.db.query(Disponibilidade)
                    .filter(
                        and_(
                            Disponibilidade.medico_id == medico.id,
                            Disponibilidade.ativa == True,
                        )
                    )
                    .all()
                )

                logger.debug(
                    f"Disponibilidades encontradas para médico | medico_id={medico.id} | "
                    f"total_disponibilidades={len(disponibilidades)}"
                )

                # Gera horários disponíveis para cada dia no período
                data_atual = data_inicio
                horarios_medico = 0
                
                while data_atual <= data_fim:
                    dia_semana = data_atual.weekday()

                    # Encontra disponibilidade para este dia da semana
                    disp = next(
                        (d for d in disponibilidades if d.dia_semana == dia_semana),
                        None,
                    )

                    if disp:
                        # Gera slots de horário dentro da disponibilidade
                        hora_atual = disp.hora_inicio
                        while hora_atual < disp.hora_fim:
                            data_hora = datetime.combine(data_atual.date(), hora_atual)

                            # Verifica se está disponível (sem conflitos)
                            if self._validar_disponibilidade(
                                medico.id, data_hora, settings.default_consultation_duration_minutes
                            ):
                                horarios_disponiveis.append(
                                    {
                                        "data_hora": data_hora,
                                        "medico_id": medico.id,
                                        "medico_nome": medico.nome,
                                        "especialidade": medico.especialidade.nome
                                        if medico.especialidade
                                        else "",
                                    }
                                )
                                horarios_medico += 1

                            # Avança para próximo slot
                            hora_atual = (
                                datetime.combine(date.today(), hora_atual)
                                + timedelta(minutes=settings.consultation_interval_minutes)
                            ).time()

                    data_atual += timedelta(days=1)
                
                logger.debug(
                    f"Horários gerados para médico | medico_id={medico.id} | "
                    f"total_horarios={horarios_medico}"
                )

            logger.info(
                f"Busca de horários disponíveis concluída | total_horarios={len(horarios_disponiveis)} | "
                f"medico_id={medico_id} | especialidade_id={especialidade_id}"
            )
            
            return horarios_disponiveis

        except Exception as e:
            logger.exception(
                f"Erro ao buscar horários disponíveis | medico_id={medico_id} | "
                f"especialidade_id={especialidade_id} | erro={str(e)}"
            )
            return []


