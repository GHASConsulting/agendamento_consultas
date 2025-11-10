"""
Rotas da API para médicos e especialidades.
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from app.database.manager import get_db
from app.schemas.schemas import Medico, MedicoCreate, MedicoUpdate, Especialidade, EspecialidadeCreate
from app.services.medico_service import MedicoService, EspecialidadeService

router = APIRouter(prefix="/medicos", tags=["medicos"])


@router.post("", response_model=Medico, status_code=status.HTTP_201_CREATED)
async def criar_medico(medico: MedicoCreate, db: Session = Depends(get_db)):
    """Cria um novo médico."""
    dados = medico.model_dump()
    logger.info(
        f"[MEDICO] Requisição para criar médico | nome={dados.get('nome')} | "
        f"crm={dados.get('crm')} | especialidade_id={dados.get('especialidade_id')}"
    )
    
    try:
        service = MedicoService(db)
        medico_criado = service.criar_medico(dados)

        if not medico_criado:
            logger.warning(
                f"[MEDICO] Falha ao criar médico | nome={dados.get('nome')} | "
                f"crm={dados.get('crm')} | motivo=CRM já está em uso"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível criar o médico. CRM pode já estar em uso.",
            )

        logger.success(
            f"[MEDICO] Médico criado com sucesso | medico_id={medico_criado.id} | "
            f"nome={medico_criado.nome} | crm={medico_criado.crm} | "
            f"especialidade_id={medico_criado.especialidade_id}"
        )
        return medico_criado

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[MEDICO] Erro ao criar médico | nome={dados.get('nome')} | crm={dados.get('crm')} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar médico",
        )


@router.get("", response_model=List[Medico])
async def listar_medicos(
    skip: int = 0,
    limit: int = 100,
    especialidade_id: Optional[int] = None,
    ativo: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Lista médicos com filtros opcionais."""
    logger.info(
        f"[MEDICO] Requisição para listar médicos | skip={skip} | limit={limit} | "
        f"especialidade_id={especialidade_id} | ativo={ativo}"
    )
    
    try:
        service = MedicoService(db)
        medicos = service.listar_medicos(
            skip=skip, limit=limit, especialidade_id=especialidade_id, ativo=ativo
        )
        
        logger.success(
            f"[MEDICO] Médicos listados com sucesso | total_encontrado={len(medicos)} | "
            f"filtros_aplicados=especialidade_id:{especialidade_id}, ativo:{ativo}"
        )
        return medicos

    except Exception as e:
        logger.exception(
            f"[MEDICO] Erro ao listar médicos | skip={skip} | limit={limit} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar médicos",
        )


@router.get("/{medico_id}", response_model=Medico)
async def buscar_medico(medico_id: int, db: Session = Depends(get_db)):
    """Busca um médico por ID."""
    logger.debug(f"[MEDICO] Requisição para buscar médico | medico_id={medico_id}")
    
    try:
        service = MedicoService(db)
        medico = service.buscar_medico(medico_id)

        if not medico:
            logger.warning(f"[MEDICO] Médico não encontrado | medico_id={medico_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado",
            )

        logger.debug(
            f"[MEDICO] Médico encontrado | medico_id={medico_id} | nome={medico.nome} | "
            f"crm={medico.crm} | ativo={medico.ativo}"
        )
        return medico

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[MEDICO] Erro ao buscar médico | medico_id={medico_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar médico",
        )


@router.put("/{medico_id}", response_model=Medico)
async def atualizar_medico(
    medico_id: int,
    medico_update: MedicoUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza um médico."""
    dados_update = medico_update.model_dump(exclude_unset=True)
    campos_atualizar = list(dados_update.keys())
    
    logger.info(
        f"[MEDICO] Requisição para atualizar médico | medico_id={medico_id} | campos={campos_atualizar}"
    )
    
    try:
        service = MedicoService(db)
        medico = service.atualizar_medico(medico_id, dados_update)

        if not medico:
            logger.warning(
                f"[MEDICO] Médico não encontrado para atualização | medico_id={medico_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado",
            )

        logger.success(
            f"[MEDICO] Médico atualizado com sucesso | medico_id={medico_id} | "
            f"nome={medico.nome} | campos_atualizados={campos_atualizar}"
        )
        return medico

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[MEDICO] Erro ao atualizar médico | medico_id={medico_id} | "
            f"campos={campos_atualizar} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao atualizar médico",
        )


# ========================================
# Rotas de Especialidades
# ========================================
@router.post("/especialidades", response_model=Especialidade, status_code=status.HTTP_201_CREATED)
async def criar_especialidade(
    especialidade: EspecialidadeCreate, db: Session = Depends(get_db)
):
    """Cria uma nova especialidade."""
    dados = especialidade.model_dump()
    logger.info(f"[ESPECIALIDADE] Requisição para criar especialidade | nome={dados.get('nome')}")
    
    try:
        service = EspecialidadeService(db)
        especialidade_criada = service.criar_especialidade(dados)

        if not especialidade_criada:
            logger.warning(
                f"[ESPECIALIDADE] Falha ao criar especialidade | nome={dados.get('nome')}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível criar a especialidade",
            )

        logger.success(
            f"[ESPECIALIDADE] Especialidade criada com sucesso | especialidade_id={especialidade_criada.id} | "
            f"nome={especialidade_criada.nome} | ativa={especialidade_criada.ativa}"
        )
        return especialidade_criada

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[ESPECIALIDADE] Erro ao criar especialidade | nome={dados.get('nome')} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao criar especialidade",
        )


@router.get("/especialidades", response_model=List[Especialidade])
async def listar_especialidades(
    skip: int = 0,
    limit: int = 100,
    ativa: Optional[bool] = None,
    db: Session = Depends(get_db),
):
    """Lista especialidades."""
    logger.info(
        f"[ESPECIALIDADE] Requisição para listar especialidades | skip={skip} | limit={limit} | ativa={ativa}"
    )
    
    try:
        service = EspecialidadeService(db)
        especialidades = service.listar_especialidades(
            skip=skip, limit=limit, ativa=ativa
        )
        
        logger.success(
            f"[ESPECIALIDADE] Especialidades listadas com sucesso | total_encontrado={len(especialidades)} | "
            f"filtro_ativa={ativa}"
        )
        return especialidades

    except Exception as e:
        logger.exception(
            f"[ESPECIALIDADE] Erro ao listar especialidades | skip={skip} | limit={limit} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar especialidades",
        )


@router.get("/especialidades/{especialidade_id}", response_model=Especialidade)
async def buscar_especialidade(especialidade_id: int, db: Session = Depends(get_db)):
    """Busca uma especialidade por ID."""
    logger.debug(f"[ESPECIALIDADE] Requisição para buscar especialidade | especialidade_id={especialidade_id}")
    
    try:
        service = EspecialidadeService(db)
        especialidade = service.buscar_especialidade(especialidade_id)

        if not especialidade:
            logger.warning(f"[ESPECIALIDADE] Especialidade não encontrada | especialidade_id={especialidade_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Especialidade não encontrada",
            )

        logger.debug(
            f"[ESPECIALIDADE] Especialidade encontrada | especialidade_id={especialidade_id} | "
            f"nome={especialidade.nome} | ativa={especialidade.ativa}"
        )
        return especialidade

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[ESPECIALIDADE] Erro ao buscar especialidade | especialidade_id={especialidade_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao buscar especialidade",
        )

