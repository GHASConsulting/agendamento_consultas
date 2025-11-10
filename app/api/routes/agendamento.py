"""
Rotas da API para agendamentos.
"""

from typing import List
from datetime import datetime, date

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database.manager import get_db
from app.schemas.schemas import (
    Agendamento,
    AgendamentoCreate,
    AgendamentoUpdate,
    AgendamentoReagendar,
    AgendamentoCancelar,
    StatusAgendamento,
)
from app.services.agendamento_service import AgendamentoService

router = APIRouter(prefix="/agendamentos", tags=["agendamentos"])


@router.post("", response_model=Agendamento, status_code=status.HTTP_201_CREATED)
async def criar_agendamento(
    agendamento: AgendamentoCreate, db: Session = Depends(get_db)
):
    """Cria um novo agendamento."""
    dados = agendamento.model_dump()
    logger.info(
        f"[AGENDAMENTO] Requisição para criar agendamento | paciente_id={dados.get('paciente_id')} | "
        f"medico_id={dados.get('medico_id')} | data_hora={dados.get('data_hora')}"
    )
    
    try:
        service = AgendamentoService(db)
        agendamento_criado = service.criar_agendamento(dados)

        if not agendamento_criado:
            logger.warning(
                f"[AGENDAMENTO] Falha ao criar agendamento | paciente_id={dados.get('paciente_id')} | "
                f"medico_id={dados.get('medico_id')} | data_hora={dados.get('data_hora')} | "
                f"motivo=Horário indisponível ou validação falhou"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível criar o agendamento. Verifique a disponibilidade do horário.",
            )

        logger.success(
            f"[AGENDAMENTO] Agendamento criado com sucesso | agendamento_id={agendamento_criado.id} | "
            f"paciente_id={agendamento_criado.paciente_id} | medico_id={agendamento_criado.medico_id} | "
            f"data_hora={agendamento_criado.data_hora} | status={agendamento_criado.status.value}"
        )
        return agendamento_criado

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao criar agendamento | paciente_id={dados.get('paciente_id')} | "
            f"medico_id={dados.get('medico_id')} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar agendamento",
        )


@router.get("", response_model=List[Agendamento])
async def listar_agendamentos(
    skip: int = 0,
    limit: int = 100,
    medico_id: int = None,
    paciente_id: int = None,
    status: StatusAgendamento = None,
    db: Session = Depends(get_db),
):
    """Lista agendamentos com filtros opcionais."""
    logger.info(
        f"[AGENDAMENTO] Requisição para listar agendamentos | skip={skip} | limit={limit} | "
        f"medico_id={medico_id} | paciente_id={paciente_id} | status={status.value if status else None}"
    )
    
    try:
        service = AgendamentoService(db)
        agendamentos = service.listar_agendamentos(
            skip=skip,
            limit=limit,
            medico_id=medico_id,
            paciente_id=paciente_id,
            status=status,
        )
        
        logger.success(
            f"[AGENDAMENTO] Agendamentos listados com sucesso | total_encontrado={len(agendamentos)} | "
            f"filtros_aplicados=medico_id:{medico_id}, paciente_id:{paciente_id}, status:{status.value if status else None}"
        )
        return agendamentos

    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao listar agendamentos | skip={skip} | limit={limit} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar agendamentos",
        )


@router.get("/{agendamento_id}", response_model=Agendamento)
async def buscar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    """Busca um agendamento por ID."""
    logger.debug(f"[AGENDAMENTO] Requisição para buscar agendamento | agendamento_id={agendamento_id}")
    
    try:
        service = AgendamentoService(db)
        agendamento = service.buscar_agendamento(agendamento_id)

        if not agendamento:
            logger.warning(f"[AGENDAMENTO] Agendamento não encontrado | agendamento_id={agendamento_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado",
            )

        logger.debug(
            f"[AGENDAMENTO] Agendamento encontrado | agendamento_id={agendamento_id} | "
            f"paciente_id={agendamento.paciente_id} | medico_id={agendamento.medico_id} | "
            f"status={agendamento.status.value}"
        )
        return agendamento

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao buscar agendamento | agendamento_id={agendamento_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar agendamento",
        )


@router.put("/{agendamento_id}", response_model=Agendamento)
async def atualizar_agendamento(
    agendamento_id: int,
    agendamento_update: AgendamentoUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza um agendamento."""
    dados_update = agendamento_update.model_dump(exclude_unset=True)
    campos_atualizar = list(dados_update.keys())
    
    logger.info(
        f"[AGENDAMENTO] Requisição para atualizar agendamento | agendamento_id={agendamento_id} | "
        f"campos={campos_atualizar}"
    )
    
    try:
        service = AgendamentoService(db)
        agendamento = service.buscar_agendamento(agendamento_id)

        if not agendamento:
            logger.warning(
                f"[AGENDAMENTO] Agendamento não encontrado para atualização | agendamento_id={agendamento_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado",
            )

        # Armazena valores antigos para log
        valores_antigos = {
            "status": agendamento.status.value,
            "observacoes": agendamento.observacoes,
        }

        # Atualiza campos
        if dados_update:
            for key, value in dados_update.items():
                setattr(agendamento, key, value)

            db.commit()
            db.refresh(agendamento)
            
            # Log das mudanças
            mudancas = []
            for campo in ["status", "observacoes"]:
                if campo in dados_update:
                    valor_antigo = valores_antigos.get(campo)
                    valor_novo = getattr(agendamento, campo)
                    if campo == "status":
                        valor_novo = valor_novo.value if hasattr(valor_novo, 'value') else valor_novo
                    if valor_antigo != valor_novo:
                        mudancas.append(f"{campo}: {valor_antigo} -> {valor_novo}")

            logger.success(
                f"[AGENDAMENTO] Agendamento atualizado com sucesso | agendamento_id={agendamento_id} | "
                f"mudancas={', '.join(mudancas) if mudancas else 'Nenhuma'}"
            )
        else:
            logger.debug(f"[AGENDAMENTO] Nenhum campo para atualizar | agendamento_id={agendamento_id}")

        return agendamento

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao atualizar agendamento | agendamento_id={agendamento_id} | "
            f"campos={campos_atualizar} | erro={str(e)}"
        )
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar agendamento",
        )


@router.post("/{agendamento_id}/reagendar", response_model=Agendamento)
async def reagendar_agendamento(
    agendamento_id: int,
    reagendamento: AgendamentoReagendar,
    db: Session = Depends(get_db),
):
    """Reagenda um agendamento."""
    logger.info(
        f"[AGENDAMENTO] Requisição para reagendar agendamento | agendamento_id={agendamento_id} | "
        f"nova_data_hora={reagendamento.nova_data_hora} | motivo={reagendamento.motivo or 'Não informado'}"
    )
    
    try:
        service = AgendamentoService(db)
        agendamento = service.reagendar(
            agendamento_id, reagendamento.nova_data_hora, reagendamento.motivo
        )

        if not agendamento:
            logger.warning(
                f"[AGENDAMENTO] Falha ao reagendar agendamento | agendamento_id={agendamento_id} | "
                f"nova_data_hora={reagendamento.nova_data_hora} | motivo=Horário indisponível ou validação falhou"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível reagendar. Verifique a disponibilidade do novo horário.",
            )

        logger.success(
            f"[AGENDAMENTO] Agendamento reagendado com sucesso | agendamento_id={agendamento.id} | "
            f"data_hora_antiga={agendamento.data_hora} | nova_data_hora={reagendamento.nova_data_hora} | "
            f"status={agendamento.status.value}"
        )
        return agendamento

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao reagendar agendamento | agendamento_id={agendamento_id} | "
            f"nova_data_hora={reagendamento.nova_data_hora} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao reagendar agendamento",
        )


@router.post("/{agendamento_id}/cancelar", response_model=Agendamento)
async def cancelar_agendamento(
    agendamento_id: int,
    cancelamento: AgendamentoCancelar,
    db: Session = Depends(get_db),
):
    """Cancela um agendamento."""
    logger.info(
        f"[AGENDAMENTO] Requisição para cancelar agendamento | agendamento_id={agendamento_id} | "
        f"motivo={cancelamento.motivo or 'Não informado'}"
    )
    
    try:
        service = AgendamentoService(db)
        agendamento = service.cancelar(agendamento_id, cancelamento.motivo)

        if not agendamento:
            logger.warning(f"[AGENDAMENTO] Agendamento não encontrado para cancelamento | agendamento_id={agendamento_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado",
            )

        logger.success(
            f"[AGENDAMENTO] Agendamento cancelado com sucesso | agendamento_id={agendamento.id} | "
            f"paciente_id={agendamento.paciente_id} | medico_id={agendamento.medico_id} | "
            f"data_hora={agendamento.data_hora} | status={agendamento.status.value} | "
            f"motivo={cancelamento.motivo or 'Não informado'}"
        )
        return agendamento

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao cancelar agendamento | agendamento_id={agendamento_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao cancelar agendamento",
        )


@router.post("/{agendamento_id}/confirmar", response_model=Agendamento)
async def confirmar_agendamento(agendamento_id: int, db: Session = Depends(get_db)):
    """Confirma um agendamento."""
    logger.info(f"[AGENDAMENTO] Requisição para confirmar agendamento | agendamento_id={agendamento_id}")
    
    try:
        service = AgendamentoService(db)
        agendamento = service.confirmar(agendamento_id)

        if not agendamento:
            logger.warning(f"[AGENDAMENTO] Agendamento não encontrado para confirmação | agendamento_id={agendamento_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agendamento não encontrado",
            )

        logger.success(
            f"[AGENDAMENTO] Agendamento confirmado com sucesso | agendamento_id={agendamento.id} | "
            f"paciente_id={agendamento.paciente_id} | medico_id={agendamento.medico_id} | "
            f"data_hora={agendamento.data_hora} | status={agendamento.status.value}"
        )
        return agendamento

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[AGENDAMENTO] Erro ao confirmar agendamento | agendamento_id={agendamento_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao confirmar agendamento",
        )

