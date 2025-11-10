"""
Rotas da API para pacientes.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database.manager import get_db
from app.schemas.schemas import Paciente, PacienteCreate, PacienteUpdate
from app.services.paciente_service import PacienteService

router = APIRouter(prefix="/pacientes", tags=["pacientes"])


@router.post("", response_model=Paciente, status_code=status.HTTP_201_CREATED)
async def criar_paciente(paciente: PacienteCreate, db: Session = Depends(get_db)):
    """Cria um novo paciente."""
    dados = paciente.model_dump()
    logger.info(
        f"[PACIENTE] Requisição para criar paciente | nome={dados.get('nome')} | "
        f"telefone={dados.get('telefone')} | cpf={dados.get('cpf') or 'Não informado'}"
    )
    
    try:
        service = PacienteService(db)
        paciente_criado = service.criar_paciente(dados)

        if not paciente_criado:
            logger.warning(
                f"[PACIENTE] Falha ao criar paciente | nome={dados.get('nome')} | "
                f"telefone={dados.get('telefone')} | motivo=Paciente já existe ou dados inválidos"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível criar o paciente",
            )

        logger.success(
            f"[PACIENTE] Paciente criado com sucesso | paciente_id={paciente_criado.id} | "
            f"nome={paciente_criado.nome} | telefone={paciente_criado.telefone}"
        )
        return paciente_criado

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[PACIENTE] Erro ao criar paciente | nome={dados.get('nome')} | "
            f"telefone={dados.get('telefone')} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar paciente",
        )


@router.get("", response_model=List[Paciente])
async def listar_pacientes(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Lista pacientes."""
    logger.info(f"[PACIENTE] Requisição para listar pacientes | skip={skip} | limit={limit}")
    
    try:
        service = PacienteService(db)
        pacientes = service.listar_pacientes(skip=skip, limit=limit)
        
        logger.success(
            f"[PACIENTE] Pacientes listados com sucesso | total_encontrado={len(pacientes)} | "
            f"skip={skip} | limit={limit}"
        )
        return pacientes

    except Exception as e:
        logger.exception(
            f"[PACIENTE] Erro ao listar pacientes | skip={skip} | limit={limit} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar pacientes",
        )


@router.get("/{paciente_id}", response_model=Paciente)
async def buscar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    """Busca um paciente por ID."""
    logger.debug(f"[PACIENTE] Requisição para buscar paciente | paciente_id={paciente_id}")
    
    try:
        service = PacienteService(db)
        paciente = service.buscar_paciente(paciente_id)

        if not paciente:
            logger.warning(f"[PACIENTE] Paciente não encontrado | paciente_id={paciente_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente não encontrado",
            )

        logger.debug(
            f"[PACIENTE] Paciente encontrado | paciente_id={paciente_id} | nome={paciente.nome} | "
            f"telefone={paciente.telefone}"
        )
        return paciente

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[PACIENTE] Erro ao buscar paciente | paciente_id={paciente_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar paciente",
        )


@router.put("/{paciente_id}", response_model=Paciente)
async def atualizar_paciente(
    paciente_id: int,
    paciente_update: PacienteUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza um paciente."""
    dados_update = paciente_update.model_dump(exclude_unset=True)
    campos_atualizar = list(dados_update.keys())
    
    logger.info(
        f"[PACIENTE] Requisição para atualizar paciente | paciente_id={paciente_id} | "
        f"campos={campos_atualizar}"
    )
    
    try:
        service = PacienteService(db)
        paciente = service.atualizar_paciente(paciente_id, dados_update)

        if not paciente:
            logger.warning(
                f"[PACIENTE] Paciente não encontrado para atualização | paciente_id={paciente_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente não encontrado",
            )

        logger.success(
            f"[PACIENTE] Paciente atualizado com sucesso | paciente_id={paciente_id} | "
            f"nome={paciente.nome} | campos_atualizados={campos_atualizar}"
        )
        return paciente

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[PACIENTE] Erro ao atualizar paciente | paciente_id={paciente_id} | "
            f"campos={campos_atualizar} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar paciente",
        )


@router.delete("/{paciente_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deletar_paciente(paciente_id: int, db: Session = Depends(get_db)):
    """Deleta um paciente."""
    logger.info(f"[PACIENTE] Requisição para deletar paciente | paciente_id={paciente_id}")
    
    try:
        service = PacienteService(db)
        sucesso = service.deletar_paciente(paciente_id)

        if not sucesso:
            logger.warning(
                f"[PACIENTE] Falha ao deletar paciente | paciente_id={paciente_id} | "
                f"motivo=Paciente não encontrado ou possui agendamentos associados"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente não encontrado ou possui agendamentos associados",
            )

        logger.success(f"[PACIENTE] Paciente deletado com sucesso | paciente_id={paciente_id}")
        return None

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[PACIENTE] Erro ao deletar paciente | paciente_id={paciente_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao deletar paciente",
        )

