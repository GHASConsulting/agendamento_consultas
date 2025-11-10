"""
Serviço para gestão de pacientes.

Este serviço gerencia:
- CRUD de pacientes
- Busca por telefone ou CPF
- Validação de dados
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from loguru import logger
from sqlalchemy.orm import Session

from app.database.models import Paciente, Agendamento


class PacienteService:
    """Serviço para gestão de pacientes"""

    def __init__(self, db: Session):
        self.db = db

    def criar_paciente(self, dados: Dict[str, Any]) -> Optional[Paciente]:
        """
        Cria um novo paciente.
        
        Se já existir paciente com o mesmo telefone, retorna o existente.
        
        Args:
            dados: Dicionário com dados do paciente (nome, telefone, email, cpf, etc.)
            
        Returns:
            Paciente criado ou existente, None em caso de erro
        """
        telefone = dados.get("telefone")
        nome = dados.get("nome")
        
        logger.info(
            f"Iniciando criação de paciente | nome={nome} | telefone={telefone}"
        )
        
        try:
            # Verifica se já existe paciente com telefone
            logger.debug(f"Verificando se paciente já existe | telefone={telefone}")
            paciente_existente = (
                self.db.query(Paciente)
                .filter(Paciente.telefone == telefone)
                .first()
            )

            if paciente_existente:
                logger.warning(
                    f"Paciente já existe com este telefone | paciente_id={paciente_existente.id} | "
                    f"telefone={telefone} | nome_existente={paciente_existente.nome}"
                )
                return paciente_existente

            logger.debug("Paciente não encontrado, criando novo registro")
            
            # Cria novo paciente
            paciente = Paciente(
                nome=nome,
                telefone=telefone,
                email=dados.get("email"),
                cpf=dados.get("cpf"),
                data_nascimento=dados.get("data_nascimento"),
            )

            self.db.add(paciente)
            self.db.commit()
            self.db.refresh(paciente)

            logger.success(
                f"Paciente criado com sucesso | paciente_id={paciente.id} | "
                f"nome={paciente.nome} | telefone={paciente.telefone} | "
                f"email={paciente.email or 'Não informado'} | cpf={'Informado' if paciente.cpf else 'Não informado'}"
            )
            return paciente

        except KeyError as e:
            logger.error(
                f"Campo obrigatório ausente ao criar paciente | campo={str(e)} | "
                f"dados_recebidos={list(dados.keys())}"
            )
            self.db.rollback()
            return None
        except Exception as e:
            logger.exception(
                f"Erro inesperado ao criar paciente | nome={nome} | telefone={telefone} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def buscar_paciente(self, paciente_id: int) -> Optional[Paciente]:
        """
        Busca um paciente por ID.
        
        Args:
            paciente_id: ID do paciente a ser buscado
            
        Returns:
            Paciente encontrado ou None
        """
        logger.debug(f"Buscando paciente | paciente_id={paciente_id}")
        
        try:
            paciente = self.db.query(Paciente).filter(Paciente.id == paciente_id).first()
            
            if paciente:
                logger.debug(
                    f"Paciente encontrado | paciente_id={paciente_id} | "
                    f"nome={paciente.nome} | telefone={paciente.telefone}"
                )
            else:
                logger.warning(f"Paciente não encontrado | paciente_id={paciente_id}")
            
            return paciente
            
        except Exception as e:
            logger.exception(
                f"Erro ao buscar paciente | paciente_id={paciente_id} | erro={str(e)}"
            )
            return None

    def buscar_paciente_por_telefone(self, telefone: str) -> Optional[Paciente]:
        """
        Busca um paciente por telefone.
        
        Args:
            telefone: Número de telefone do paciente
            
        Returns:
            Paciente encontrado ou None
        """
        logger.debug(f"Buscando paciente por telefone | telefone={telefone}")
        
        try:
            paciente = (
                self.db.query(Paciente).filter(Paciente.telefone == telefone).first()
            )
            
            if paciente:
                logger.debug(
                    f"Paciente encontrado por telefone | paciente_id={paciente.id} | "
                    f"nome={paciente.nome} | telefone={telefone}"
                )
            else:
                logger.debug(f"Paciente não encontrado por telefone | telefone={telefone}")
            
            return paciente
            
        except Exception as e:
            logger.exception(
                f"Erro ao buscar paciente por telefone | telefone={telefone} | erro={str(e)}"
            )
            return None

    def buscar_paciente_por_cpf(self, cpf: str) -> Optional[Paciente]:
        """
        Busca um paciente por CPF.
        
        Args:
            cpf: CPF do paciente
            
        Returns:
            Paciente encontrado ou None
        """
        logger.debug(f"Buscando paciente por CPF | cpf={cpf}")
        
        try:
            paciente = self.db.query(Paciente).filter(Paciente.cpf == cpf).first()
            
            if paciente:
                logger.debug(
                    f"Paciente encontrado por CPF | paciente_id={paciente.id} | "
                    f"nome={paciente.nome} | cpf={cpf}"
                )
            else:
                logger.debug(f"Paciente não encontrado por CPF | cpf={cpf}")
            
            return paciente
            
        except Exception as e:
            logger.exception(
                f"Erro ao buscar paciente por CPF | cpf={cpf} | erro={str(e)}"
            )
            return None

    def listar_pacientes(self, skip: int = 0, limit: int = 100) -> List[Paciente]:
        """
        Lista pacientes com paginação.
        
        Args:
            skip: Número de registros para pular (paginação)
            limit: Número máximo de registros a retornar
            
        Returns:
            Lista de pacientes encontrados
        """
        logger.debug(f"Listando pacientes | skip={skip} | limit={limit}")
        
        try:
            pacientes = self.db.query(Paciente).offset(skip).limit(limit).all()
            
            logger.info(
                f"Pacientes listados com sucesso | total_encontrado={len(pacientes)} | "
                f"skip={skip} | limit={limit}"
            )
            
            return pacientes
            
        except Exception as e:
            logger.exception(
                f"Erro ao listar pacientes | skip={skip} | limit={limit} | erro={str(e)}"
            )
            return []

    def atualizar_paciente(
        self, paciente_id: int, dados: Dict[str, Any]
    ) -> Optional[Paciente]:
        """
        Atualiza dados de um paciente.
        
        Args:
            paciente_id: ID do paciente a ser atualizado
            dados: Dicionário com campos a serem atualizados
            
        Returns:
            Paciente atualizado ou None em caso de erro
        """
        campos_atualizar = list(dados.keys())
        logger.info(
            f"Iniciando atualização de paciente | paciente_id={paciente_id} | "
            f"campos={campos_atualizar}"
        )
        
        try:
            paciente = self.buscar_paciente(paciente_id)
            if not paciente:
                logger.warning(f"Paciente não encontrado para atualização | paciente_id={paciente_id}")
                return None

            # Armazena valores antigos para log
            valores_antigos = {
                "nome": paciente.nome,
                "telefone": paciente.telefone,
                "email": paciente.email,
                "cpf": paciente.cpf,
            }

            # Atualiza campos fornecidos
            if "nome" in dados:
                paciente.nome = dados["nome"]
            if "telefone" in dados:
                paciente.telefone = dados["telefone"]
            if "email" in dados:
                paciente.email = dados["email"]
            if "cpf" in dados:
                paciente.cpf = dados["cpf"]
            if "data_nascimento" in dados:
                paciente.data_nascimento = dados["data_nascimento"]

            paciente.atualizado_em = datetime.now()

            self.db.commit()
            self.db.refresh(paciente)

            # Log das mudanças
            mudancas = []
            for campo in ["nome", "telefone", "email", "cpf"]:
                if campo in dados and valores_antigos.get(campo) != getattr(paciente, campo):
                    mudancas.append(f"{campo}: {valores_antigos.get(campo)} -> {getattr(paciente, campo)}")

            logger.success(
                f"Paciente atualizado com sucesso | paciente_id={paciente_id} | "
                f"mudancas={', '.join(mudancas) if mudancas else 'Nenhuma'} | "
                f"atualizado_em={paciente.atualizado_em}"
            )
            return paciente

        except Exception as e:
            logger.exception(
                f"Erro ao atualizar paciente | paciente_id={paciente_id} | "
                f"campos={campos_atualizar} | erro={str(e)}"
            )
            self.db.rollback()
            return None

    def deletar_paciente(self, paciente_id: int) -> bool:
        """
        Deleta um paciente.
        
        Não permite deletar paciente que possui agendamentos associados.
        
        Args:
            paciente_id: ID do paciente a ser deletado
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        logger.info(f"Iniciando exclusão de paciente | paciente_id={paciente_id}")
        
        try:
            paciente = self.buscar_paciente(paciente_id)
            if not paciente:
                logger.warning(f"Paciente não encontrado para exclusão | paciente_id={paciente_id}")
                return False

            logger.debug(
                f"Paciente encontrado | paciente_id={paciente_id} | "
                f"nome={paciente.nome} | telefone={paciente.telefone}"
            )

            # Verifica se tem agendamentos
            agendamentos = (
                self.db.query(Agendamento)
                .filter(Agendamento.paciente_id == paciente_id)
                .count()
            )
            
            if agendamentos > 0:
                logger.warning(
                    f"Não é possível deletar paciente com agendamentos | paciente_id={paciente_id} | "
                    f"nome={paciente.nome} | total_agendamentos={agendamentos}"
                )
                return False

            nome_paciente = paciente.nome
            telefone_paciente = paciente.telefone
            
            self.db.delete(paciente)
            self.db.commit()

            logger.success(
                f"Paciente deletado com sucesso | paciente_id={paciente_id} | "
                f"nome={nome_paciente} | telefone={telefone_paciente}"
            )
            return True

        except Exception as e:
            logger.exception(
                f"Erro ao deletar paciente | paciente_id={paciente_id} | erro={str(e)}"
            )
            self.db.rollback()
            return False

