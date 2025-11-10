"""
Rotas da API para consulta de disponibilidade.
"""

from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from loguru import logger
from sqlalchemy.orm import Session

from app.database.manager import get_db
from app.schemas.schemas import HorarioDisponivel, DisponibilidadeResponse
from app.services.agendamento_service import AgendamentoService

router = APIRouter(prefix="/disponibilidade", tags=["disponibilidade"])


@router.get("/horarios", response_model=DisponibilidadeResponse)
async def buscar_horarios_disponiveis(
    medico_id: int = Query(None, description="ID do médico"),
    especialidade_id: int = Query(None, description="ID da especialidade"),
    data_inicio: datetime = Query(None, description="Data de início da busca"),
    data_fim: datetime = Query(None, description="Data de fim da busca"),
    db: Session = Depends(get_db),
):
    """Busca horários disponíveis para agendamento."""
    logger.info(
        f"[DISPONIBILIDADE] Requisição para buscar horários disponíveis | medico_id={medico_id} | "
        f"especialidade_id={especialidade_id} | data_inicio={data_inicio} | data_fim={data_fim}"
    )
    
    try:
        service = AgendamentoService(db)

        # Define período padrão se não fornecido
        if not data_inicio:
            data_inicio = datetime.now()
        if not data_fim:
            data_fim = data_inicio + timedelta(days=30)

        logger.debug(
            f"[DISPONIBILIDADE] Período de busca | data_inicio={data_inicio} | data_fim={data_fim} | "
            f"dias_total={(data_fim - data_inicio).days}"
        )

        horarios = service.buscar_horarios_disponiveis(
            medico_id=medico_id,
            especialidade_id=especialidade_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Converte para formato de resposta
        horarios_disponiveis = [
            HorarioDisponivel(
                data_hora=h["data_hora"],
                medico_id=h["medico_id"],
                medico_nome=h["medico_nome"],
                especialidade=h["especialidade"],
            )
            for h in horarios
        ]

        logger.success(
            f"[DISPONIBILIDADE] Horários disponíveis encontrados | total={len(horarios_disponiveis)} | "
            f"medico_id={medico_id} | especialidade_id={especialidade_id} | "
            f"periodo={data_inicio} a {data_fim}"
        )

        return DisponibilidadeResponse(
            horarios_disponiveis=horarios_disponiveis, total=len(horarios_disponiveis)
        )

    except Exception as e:
        logger.exception(
            f"[DISPONIBILIDADE] Erro ao buscar horários disponíveis | medico_id={medico_id} | "
            f"especialidade_id={especialidade_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar horários disponíveis",
        )

