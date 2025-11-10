"""
Serviço para gestão de médicos e especialidades.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.database.models import Medico, Especialidade


class MedicoService:
    """Serviço para gestão de médicos"""

    def __init__(self, db: Session):
        self.db = db

    def criar_medico(self, dados: Dict[str, Any]) -> Optional[Medico]:
        """
        Cria um novo médico.
        
        Args:
            dados: Dicionário com dados do médico (nome, crm, especialidade_id, etc.)
            
        Returns:
            Médico criado ou None em caso de erro ou CRM duplicado
        """
        crm = dados.get("crm")
        nome = dados.get("nome")
        especialidade_id = dados.get("especialidade_id")
        
        logger.info(
            f"Iniciando criação de médico | nome={nome} | crm={crm} | "
            f"especialidade_id={especialidade_id}"
        )
        
        try:
            # Verifica se CRM já existe
            logger.debug(f"Verificando se médico já existe | crm={crm}")
            medico_existente = (
                self.db.query(Medico).filter(Medico.crm == crm).first()
            )
            if medico_existente:
                logger.warning(
                    f"Médico já existe com este CRM | medico_id={medico_existente.id} | "
                    f"crm={crm} | nome_existente={medico_existente.nome}"
                )
                return None

            logger.debug("CRM disponível, criando novo médico")
            
            medico = Medico(
                nome=nome,
                crm=crm,
                telefone=dados.get("telefone"),
                email=dados.get("email"),
                especialidade_id=especialidade_id,
            )

            self.db.add(medico)
            self.db.commit()
            self.db.refresh(medico)

            logger.success(
                f"Médico criado com sucesso | medico_id={medico.id} | nome={medico.nome} | "
                f"crm={medico.crm} | especialidade_id={medico.especialidade_id} | "
                f"ativo={medico.ativo}"
            )
            return medico

        except KeyError as e:
            logger.error(
                f"Campo obrigatório ausente ao criar médico | campo={str(e)} | "
                f"dados_recebidos={list(dados.keys())}"
            )
            self.db.rollback()
            return None
        except Exception as e:
            logger.exception(
                f"Erro inesperado ao criar médico | nome={nome} | crm={crm} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def buscar_medico(self, medico_id: int) -> Optional[Medico]:
        """
        Busca um médico por ID.
        
        Args:
            medico_id: ID do médico a ser buscado
            
        Returns:
            Médico encontrado ou None
        """
        logger.debug(f"Buscando médico | medico_id={medico_id}")
        
        try:
            medico = (
                self.db.query(Medico).filter(Medico.id == medico_id).first()
            )
            
            if medico:
                logger.debug(
                    f"Médico encontrado | medico_id={medico_id} | nome={medico.nome} | "
                    f"crm={medico.crm} | especialidade_id={medico.especialidade_id} | "
                    f"ativo={medico.ativo}"
                )
            else:
                logger.warning(f"Médico não encontrado | medico_id={medico_id}")
            
            return medico
            
        except Exception as e:
            logger.exception(
                f"Erro ao buscar médico | medico_id={medico_id} | erro={str(e)}"
            )
            return None

    def listar_medicos(
        self,
        skip: int = 0,
        limit: int = 100,
        especialidade_id: Optional[int] = None,
        ativo: Optional[bool] = None,
    ) -> List[Medico]:
        """
        Lista médicos com filtros opcionais.
        
        Args:
            skip: Número de registros para pular (paginação)
            limit: Número máximo de registros a retornar
            especialidade_id: Filtrar por especialidade específica
            ativo: Filtrar por status ativo/inativo
            
        Returns:
            Lista de médicos encontrados
        """
        logger.debug(
            f"Listando médicos | skip={skip} | limit={limit} | "
            f"especialidade_id={especialidade_id} | ativo={ativo}"
        )
        
        try:
            query = self.db.query(Medico)

            if especialidade_id:
                query = query.filter(Medico.especialidade_id == especialidade_id)
            if ativo is not None:
                query = query.filter(Medico.ativo == ativo)

            medicos = query.offset(skip).limit(limit).all()
            
            logger.info(
                f"Médicos listados com sucesso | total_encontrado={len(medicos)} | "
                f"filtros_aplicados=especialidade_id:{especialidade_id}, ativo:{ativo}"
            )
            
            return medicos
            
        except Exception as e:
            logger.exception(
                f"Erro ao listar médicos | skip={skip} | limit={limit} | erro={str(e)}"
            )
            return []

    def atualizar_medico(
        self, medico_id: int, dados: Dict[str, Any]
    ) -> Optional[Medico]:
        """
        Atualiza dados de um médico.
        
        Args:
            medico_id: ID do médico a ser atualizado
            dados: Dicionário com campos a serem atualizados
            
        Returns:
            Médico atualizado ou None em caso de erro
        """
        campos_atualizar = list(dados.keys())
        logger.info(
            f"Iniciando atualização de médico | medico_id={medico_id} | "
            f"campos={campos_atualizar}"
        )
        
        try:
            medico = self.buscar_medico(medico_id)
            if not medico:
                logger.warning(f"Médico não encontrado para atualização | medico_id={medico_id}")
                return None

            # Armazena valores antigos para log
            valores_antigos = {
                "nome": medico.nome,
                "telefone": medico.telefone,
                "email": medico.email,
                "ativo": medico.ativo,
            }

            # Atualiza campos fornecidos
            if "nome" in dados:
                medico.nome = dados["nome"]
            if "telefone" in dados:
                medico.telefone = dados["telefone"]
            if "email" in dados:
                medico.email = dados["email"]
            if "ativo" in dados:
                medico.ativo = dados["ativo"]

            medico.atualizado_em = datetime.now()
            self.db.commit()
            self.db.refresh(medico)

            # Log das mudanças
            mudancas = []
            for campo in ["nome", "telefone", "email", "ativo"]:
                if campo in dados and valores_antigos.get(campo) != getattr(medico, campo):
                    mudancas.append(f"{campo}: {valores_antigos.get(campo)} -> {getattr(medico, campo)}")

            logger.success(
                f"Médico atualizado com sucesso | medico_id={medico_id} | "
                f"mudancas={', '.join(mudancas) if mudancas else 'Nenhuma'} | "
                f"atualizado_em={medico.atualizado_em}"
            )
            return medico

        except Exception as e:
            logger.exception(
                f"Erro ao atualizar médico | medico_id={medico_id} | "
                f"campos={campos_atualizar} | erro={str(e)}"
            )
            self.db.rollback()
            return None


class EspecialidadeService:
    """Serviço para gestão de especialidades"""

    def __init__(self, db: Session):
        self.db = db

    def criar_especialidade(self, dados: Dict[str, Any]) -> Optional[Especialidade]:
        """
        Cria uma nova especialidade.
        
        Se já existir especialidade com o mesmo nome, retorna a existente.
        
        Args:
            dados: Dicionário com dados da especialidade (nome, descricao)
            
        Returns:
            Especialidade criada ou existente, None em caso de erro
        """
        nome = dados.get("nome")
        
        logger.info(f"Iniciando criação de especialidade | nome={nome}")
        
        try:
            # Verifica se especialidade já existe
            logger.debug(f"Verificando se especialidade já existe | nome={nome}")
            especialidade_existente = (
                self.db.query(Especialidade)
                .filter(Especialidade.nome == nome)
                .first()
            )
            if especialidade_existente:
                logger.warning(
                    f"Especialidade já existe | especialidade_id={especialidade_existente.id} | "
                    f"nome={nome} | ativa={especialidade_existente.ativa}"
                )
                return especialidade_existente

            logger.debug("Especialidade não encontrada, criando novo registro")
            
            especialidade = Especialidade(
                nome=nome, descricao=dados.get("descricao")
            )

            self.db.add(especialidade)
            self.db.commit()
            self.db.refresh(especialidade)

            logger.success(
                f"Especialidade criada com sucesso | especialidade_id={especialidade.id} | "
                f"nome={especialidade.nome} | ativa={especialidade.ativa}"
            )
            return especialidade

        except KeyError as e:
            logger.error(
                f"Campo obrigatório ausente ao criar especialidade | campo={str(e)} | "
                f"dados_recebidos={list(dados.keys())}"
            )
            self.db.rollback()
            return None
        except Exception as e:
            logger.exception(
                f"Erro inesperado ao criar especialidade | nome={nome} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def buscar_especialidade(self, especialidade_id: int) -> Optional[Especialidade]:
        """
        Busca uma especialidade por ID.
        
        Args:
            especialidade_id: ID da especialidade a ser buscada
            
        Returns:
            Especialidade encontrada ou None
        """
        logger.debug(f"Buscando especialidade | especialidade_id={especialidade_id}")
        
        try:
            especialidade = (
                self.db.query(Especialidade)
                .filter(Especialidade.id == especialidade_id)
                .first()
            )
            
            if especialidade:
                logger.debug(
                    f"Especialidade encontrada | especialidade_id={especialidade_id} | "
                    f"nome={especialidade.nome} | ativa={especialidade.ativa}"
                )
            else:
                logger.warning(f"Especialidade não encontrada | especialidade_id={especialidade_id}")
            
            return especialidade
            
        except Exception as e:
            logger.exception(
                f"Erro ao buscar especialidade | especialidade_id={especialidade_id} | erro={str(e)}"
            )
            return None

    def listar_especialidades(
        self, skip: int = 0, limit: int = 100, ativa: Optional[bool] = None
    ) -> List[Especialidade]:
        """
        Lista especialidades com filtros opcionais.
        
        Args:
            skip: Número de registros para pular (paginação)
            limit: Número máximo de registros a retornar
            ativa: Filtrar por status ativa/inativa
            
        Returns:
            Lista de especialidades encontradas
        """
        logger.debug(
            f"Listando especialidades | skip={skip} | limit={limit} | ativa={ativa}"
        )
        
        try:
            query = self.db.query(Especialidade)

            if ativa is not None:
                query = query.filter(Especialidade.ativa == ativa)

            especialidades = query.offset(skip).limit(limit).all()
            
            logger.info(
                f"Especialidades listadas com sucesso | total_encontrado={len(especialidades)} | "
                f"filtro_ativa={ativa}"
            )
            
            return especialidades
            
        except Exception as e:
            logger.exception(
                f"Erro ao listar especialidades | skip={skip} | limit={limit} | erro={str(e)}"
            )
            return []

