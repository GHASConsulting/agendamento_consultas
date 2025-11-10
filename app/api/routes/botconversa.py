"""
Rotas da API para integração com Botconversa - Fluxo de Agendamento.

Observação: Botconversa exige HTTPS. Utilizamos N8N/Make como proxy HTTPS para chamar estas rotas HTTP.

Este módulo implementa o fluxo completo de agendamento via Botconversa:
1. Listar especialidades disponíveis
2. Listar médicos por especialidade
3. Listar datas disponíveis do médico
4. Listar horários disponíveis na data escolhida
"""

from typing import List
from datetime import datetime, date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from loguru import logger
from sqlalchemy.orm import Session

from app.database.manager import get_db
from app.schemas.schemas import (
    EspecialidadesResponse,
    EspecialidadeBotconversa,
    MedicosResponse,
    MedicoBotconversa,
    DatasDisponiveisResponse,
    DataDisponivelBotconversa,
    HorariosDisponiveisResponse,
    HorarioDisponivelBotconversa,
    AgendamentoBotconversaCreate,
    AgendamentoConfirmacaoResponse,
)
from app.services.medico_service import MedicoService, EspecialidadeService
from app.services.agendamento_service import AgendamentoService
from app.services.paciente_service import PacienteService
from app.config.config import settings

router = APIRouter(prefix="/botconversa", tags=["botconversa"])


def formatar_data_pt_br(data: date) -> str:
    """Formata data para formato brasileiro: DD/MM/YYYY"""
    return data.strftime("%d/%m/%Y")


def obter_dia_semana_pt_br(data: date) -> str:
    """Retorna o dia da semana em português"""
    dias_semana = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]
    return dias_semana[data.weekday()]


@router.get("/especialidades", response_model=EspecialidadesResponse)
async def listar_especialidades_botconversa(
    ativa: bool = Query(True, description="Listar apenas especialidades ativas"),
    db: Session = Depends(get_db),
):
    """
    Lista especialidades disponíveis formatadas para Botconversa.

    Esta rota é chamada quando o paciente escolhe "Agendar" no Botconversa.
    Retorna uma lista de especialidades para o paciente escolher.
    """
    logger.info(
        f"[BOTCONVERSA] Requisição para listar especialidades | filtro_ativa={ativa}"
    )

    try:
        service = EspecialidadeService(db)
        especialidades_list = service.listar_especialidades(ativa=ativa)

        especialidades_formatadas = [
            EspecialidadeBotconversa(
                id=esp.id,
                nome=esp.nome,
                descricao=esp.descricao,
            )
            for esp in especialidades_list
        ]

        logger.success(
            f"[BOTCONVERSA] Especialidades listadas com sucesso | total={len(especialidades_formatadas)} | "
            f"filtro_ativa={ativa}"
        )

        return EspecialidadesResponse(
            especialidades=especialidades_formatadas,
            total=len(especialidades_formatadas),
            mensagem="Escolha uma especialidade:",
        )

    except Exception as e:
        logger.exception(
            f"[BOTCONVERSA] Erro ao listar especialidades | filtro_ativa={ativa} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar especialidades",
        )


@router.get("/medicos", response_model=MedicosResponse)
async def listar_medicos_botconversa(
    especialidade_id: int = Query(..., description="ID da especialidade escolhida"),
    db: Session = Depends(get_db),
):
    """
    Lista médicos disponíveis de uma especialidade formatados para Botconversa.

    Esta rota é chamada após o paciente escolher uma especialidade.
    Retorna uma lista de médicos daquela especialidade para o paciente escolher.
    """
    logger.info(
        f"[BOTCONVERSA] Requisição para listar médicos | especialidade_id={especialidade_id}"
    )

    try:
        # Verifica se a especialidade existe
        esp_service = EspecialidadeService(db)
        especialidade = esp_service.buscar_especialidade(especialidade_id)

        if not especialidade:
            logger.warning(
                f"[BOTCONVERSA] Especialidade não encontrada | especialidade_id={especialidade_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Especialidade não encontrada",
            )

        logger.debug(
            f"[BOTCONVERSA] Especialidade encontrada | especialidade_id={especialidade_id} | "
            f"nome={especialidade.nome}"
        )

        # Busca médicos ativos da especialidade
        medico_service = MedicoService(db)
        medicos_list = medico_service.listar_medicos(
            especialidade_id=especialidade_id,
            ativo=True,
        )

        medicos_formatados = [
            MedicoBotconversa(
                id=med.id,
                nome=med.nome,
                crm=med.crm,
                especialidade_nome=especialidade.nome,
            )
            for med in medicos_list
        ]

        if not medicos_formatados:
            logger.warning(
                f"[BOTCONVERSA] Nenhum médico ativo encontrado | especialidade_id={especialidade_id} | "
                f"especialidade_nome={especialidade.nome}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum médico ativo encontrado para a especialidade {especialidade.nome}",
            )

        logger.success(
            f"[BOTCONVERSA] Médicos listados com sucesso | especialidade_id={especialidade_id} | "
            f"especialidade_nome={especialidade.nome} | total_medicos={len(medicos_formatados)}"
        )

        return MedicosResponse(
            medicos=medicos_formatados,
            total=len(medicos_formatados),
            especialidade_nome=especialidade.nome,
            mensagem=f"Escolha um médico da especialidade {especialidade.nome}:",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[BOTCONVERSA] Erro ao listar médicos | especialidade_id={especialidade_id} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar médicos",
        )


@router.get("/datas-disponiveis", response_model=DatasDisponiveisResponse)
async def listar_datas_disponiveis_botconversa(
    medico_id: int = Query(..., description="ID do médico escolhido"),
    dias_frente: int = Query(
        90, description="Quantos dias à frente buscar", ge=1, le=180
    ),
    db: Session = Depends(get_db),
):
    """
    Lista datas disponíveis do médico formatadas para Botconversa.

    Esta rota é chamada após o paciente escolher um médico.
    Retorna as datas disponíveis baseadas nos dias da semana que o médico atende
    (ex: se atende terça, quinta e sexta, retorna todas as terças, quintas e sextas
    dentro do período configurado).
    """
    logger.info(
        f"[BOTCONVERSA] Requisição para listar datas disponíveis | medico_id={medico_id} | "
        f"dias_frente={dias_frente}"
    )

    try:
        from app.database.models import Medico, Disponibilidade
        from app.config.config import settings

        # Verifica se o médico existe e está ativo
        medico_service = MedicoService(db)
        medico = medico_service.buscar_medico(medico_id)

        if not medico:
            logger.warning(
                f"[BOTCONVERSA] Médico não encontrado | medico_id={medico_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado",
            )

        if not medico.ativo:
            logger.warning(
                f"[BOTCONVERSA] Médico inativo | medico_id={medico_id} | nome={medico.nome}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Médico não está ativo",
            )

        logger.debug(
            f"[BOTCONVERSA] Médico validado | medico_id={medico_id} | nome={medico.nome}"
        )

        # Busca disponibilidades do médico
        disponibilidades = (
            db.query(Disponibilidade)
            .filter(
                Disponibilidade.medico_id == medico_id,
                Disponibilidade.ativa == True,
            )
            .all()
        )

        if not disponibilidades:
            logger.warning(
                f"[BOTCONVERSA] Nenhuma disponibilidade configurada | medico_id={medico_id} | "
                f"nome={medico.nome}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma disponibilidade configurada para este médico",
            )

        # Extrai os dias da semana que o médico atende
        dias_semana_disponiveis = [disp.dia_semana for disp in disponibilidades]
        logger.debug(
            f"[BOTCONVERSA] Disponibilidades encontradas | medico_id={medico_id} | "
            f"total_disponibilidades={len(disponibilidades)} | dias_semana={dias_semana_disponiveis}"
        )

        # Calcula datas disponíveis
        data_inicio = datetime.now().date()
        data_fim = data_inicio + timedelta(days=dias_frente)

        # Aplica antecedência mínima
        min_advance = timedelta(hours=settings.min_advance_booking_hours)
        data_inicio = (datetime.now() + min_advance).date()

        logger.debug(
            f"[BOTCONVERSA] Período de busca | data_inicio={data_inicio} | data_fim={data_fim} | "
            f"dias_total={(data_fim - data_inicio).days}"
        )

        datas_disponiveis = []
        data_atual = data_inicio

        while data_atual <= data_fim:
            # Verifica se o dia da semana está na lista de disponibilidade
            if data_atual.weekday() in dias_semana_disponiveis:
                datas_disponiveis.append(
                    DataDisponivelBotconversa(
                        data=data_atual,
                        data_formatada=formatar_data_pt_br(data_atual),
                        dia_semana=obter_dia_semana_pt_br(data_atual),
                    )
                )

            data_atual += timedelta(days=1)

        if not datas_disponiveis:
            logger.warning(
                f"[BOTCONVERSA] Nenhuma data disponível encontrada | medico_id={medico_id} | "
                f"periodo={data_inicio} a {data_fim}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhuma data disponível encontrada no período configurado",
            )

        logger.success(
            f"[BOTCONVERSA] Datas disponíveis listadas | medico_id={medico_id} | "
            f"medico_nome={medico.nome} | total_datas={len(datas_disponiveis)} | "
            f"periodo={data_inicio} a {data_fim}"
        )

        return DatasDisponiveisResponse(
            datas=datas_disponiveis,
            total=len(datas_disponiveis),
            medico_nome=medico.nome,
            mensagem=f"Escolha uma data para consulta com Dr(a). {medico.nome}:",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[BOTCONVERSA] Erro ao listar datas disponíveis | medico_id={medico_id} | "
            f"dias_frente={dias_frente} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar datas disponíveis",
        )


@router.get("/horarios-disponiveis", response_model=HorariosDisponiveisResponse)
async def listar_horarios_disponiveis_botconversa(
    medico_id: int = Query(..., description="ID do médico escolhido"),
    data: date = Query(..., description="Data escolhida no formato YYYY-MM-DD"),
    db: Session = Depends(get_db),
):
    """
    Lista horários disponíveis na data escolhida formatados para Botconversa.

    Esta rota é chamada após o paciente escolher uma data.
    Retorna os horários disponíveis naquela data específica, respeitando:
    - Período de disponibilidade do médico naquele dia da semana
    - Intervalo entre consultas
    - Agendamentos já existentes
    """
    logger.info(
        f"[BOTCONVERSA] Requisição para listar horários disponíveis | medico_id={medico_id} | "
        f"data={data}"
    )

    try:
        from app.database.models import Medico, Disponibilidade
        from app.config.config import settings

        # Verifica se o médico existe e está ativo
        medico_service = MedicoService(db)
        medico = medico_service.buscar_medico(medico_id)

        if not medico:
            logger.warning(
                f"[BOTCONVERSA] Médico não encontrado | medico_id={medico_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado",
            )

        if not medico.ativo:
            logger.warning(
                f"[BOTCONVERSA] Médico inativo | medico_id={medico_id} | nome={medico.nome}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Médico não está ativo",
            )

        # Valida se a data não é no passado
        if data < datetime.now().date():
            logger.warning(
                f"[BOTCONVERSA] Tentativa de agendar em data passada | medico_id={medico_id} | "
                f"data={data} | hoje={datetime.now().date()}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível agendar em data passada",
            )

        # Busca disponibilidade do médico para o dia da semana
        dia_semana = data.weekday()
        disponibilidade = (
            db.query(Disponibilidade)
            .filter(
                Disponibilidade.medico_id == medico_id,
                Disponibilidade.dia_semana == dia_semana,
                Disponibilidade.ativa == True,
            )
            .first()
        )

        if not disponibilidade:
            logger.warning(
                f"[BOTCONVERSA] Médico não atende neste dia da semana | medico_id={medico_id} | "
                f"data={data} | dia_semana={dia_semana} | dia_nome={obter_dia_semana_pt_br(data)}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Médico não atende neste dia da semana ({obter_dia_semana_pt_br(data)})",
            )

        logger.debug(
            f"[BOTCONVERSA] Disponibilidade encontrada | medico_id={medico_id} | "
            f"data={data} | hora_inicio={disponibilidade.hora_inicio} | "
            f"hora_fim={disponibilidade.hora_fim}"
        )

        # Gera horários disponíveis usando o serviço de agendamento
        agendamento_service = AgendamentoService(db)

        # Calcula data/hora início e fim do dia
        data_inicio = datetime.combine(data, disponibilidade.hora_inicio)
        data_fim = datetime.combine(data, disponibilidade.hora_fim)

        logger.debug(
            f"[BOTCONVERSA] Buscando horários disponíveis | medico_id={medico_id} | "
            f"data_inicio={data_inicio} | data_fim={data_fim}"
        )

        # Busca horários disponíveis usando o método existente
        horarios = agendamento_service.buscar_horarios_disponiveis(
            medico_id=medico_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )

        # Filtra apenas horários da data escolhida
        horarios_data = [h for h in horarios if h["data_hora"].date() == data]

        if not horarios_data:
            logger.warning(
                f"[BOTCONVERSA] Nenhum horário disponível para esta data | medico_id={medico_id} | "
                f"data={data} | medico_nome={medico.nome}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Nenhum horário disponível para esta data",
            )

        # Formata horários para Botconversa
        horarios_formatados = [
            HorarioDisponivelBotconversa(
                horario=h["data_hora"].strftime("%H:%M"),
                data_hora=h["data_hora"],
            )
            for h in horarios_data
        ]

        logger.success(
            f"[BOTCONVERSA] Horários disponíveis listados | medico_id={medico_id} | "
            f"medico_nome={medico.nome} | data={data} | total_horarios={len(horarios_formatados)}"
        )

        return HorariosDisponiveisResponse(
            horarios=horarios_formatados,
            total=len(horarios_formatados),
            medico_nome=medico.nome,
            data_formatada=formatar_data_pt_br(data),
            mensagem=f"Escolha um horário para {formatar_data_pt_br(data)} ({obter_dia_semana_pt_br(data)}):",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[BOTCONVERSA] Erro ao listar horários disponíveis | medico_id={medico_id} | "
            f"data={data} | erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao listar horários disponíveis",
        )


def formatar_mensagem_confirmacao_agendamento(
    agendamento,
    medico,
    especialidade,
    paciente,
    hospital_name: str = None,
    hospital_address: str = None,
    hospital_phone: str = None,
) -> str:
    """
    Formata mensagem de confirmação de agendamento para enviar via Botconversa.
    """
    data_formatada = formatar_data_pt_br(agendamento.data_hora.date())
    hora_formatada = agendamento.data_hora.strftime("%H:%M")
    dia_semana = obter_dia_semana_pt_br(agendamento.data_hora.date())

    mensagem = f"""
✅ *Agendamento Confirmado!*

Olá *{paciente.nome}*!

Seu agendamento foi realizado com sucesso:

📋 *Detalhes da Consulta:*
• *Especialidade:* {especialidade.nome}
• *Médico(a):* Dr(a). {medico.nome}
• *CRM:* {medico.crm}
• *Data:* {data_formatada} ({dia_semana})
• *Horário:* {hora_formatada}
• *Duração:* {agendamento.duracao_minutos} minutos
"""

    if agendamento.observacoes:
        mensagem += f"• *Observações:* {agendamento.observacoes}\n"

    if hospital_name:
        mensagem += f"\n🏥 *{hospital_name}*\n"

    if hospital_address:
        mensagem += f"📍 {hospital_address}\n"

    if hospital_phone:
        mensagem += f"📞 {hospital_phone}\n"

    mensagem += """
\\. 
⚠️ *Importante:*
• Chegue com 15 minutos de antecedência
• Em caso de cancelamento, avise com pelo menos 24 horas de antecedência
• Traga um documento de identidade com foto

Obrigado por escolher nossos serviços!
"""

    return mensagem.strip()


@router.post("/criar-agendamento", response_model=AgendamentoConfirmacaoResponse)
async def criar_agendamento_botconversa(
    agendamento_data: AgendamentoBotconversaCreate,
    db: Session = Depends(get_db),
):
    """
    Cria um agendamento via Botconversa e retorna mensagem de confirmação formatada.

    Esta rota é chamada após o paciente escolher médico, data e horário.
    O fluxo:
    1. Busca ou cria paciente pelo telefone
    2. Valida disponibilidade do horário
    3. Cria o agendamento
    4. Retorna mensagem formatada para enviar via Botconversa
    """
    logger.info(
        f"[BOTCONVERSA] Requisição para criar agendamento | telefone={agendamento_data.telefone} | "
        f"medico_id={agendamento_data.medico_id} | data_hora={agendamento_data.data_hora} | "
        f"nome_paciente={agendamento_data.nome_paciente or 'Não fornecido'}"
    )

    try:
        from app.database.models import Medico, Especialidade

        # Busca ou cria paciente
        logger.debug(
            f"[BOTCONVERSA] Buscando paciente | telefone={agendamento_data.telefone}"
        )
        paciente_service = PacienteService(db)
        paciente = paciente_service.buscar_paciente_por_telefone(
            agendamento_data.telefone
        )

        paciente_criado = False
        if not paciente:
            # Cria novo paciente se não existir
            if not agendamento_data.nome_paciente:
                logger.warning(
                    f"[BOTCONVERSA] Nome do paciente obrigatório para novo cadastro | "
                    f"telefone={agendamento_data.telefone}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Nome do paciente é obrigatório para criar novo cadastro",
                )

            logger.debug(
                f"[BOTCONVERSA] Criando novo paciente | nome={agendamento_data.nome_paciente} | "
                f"telefone={agendamento_data.telefone}"
            )
            paciente_dados = {
                "nome": agendamento_data.nome_paciente,
                "telefone": agendamento_data.telefone,
            }
            paciente = paciente_service.criar_paciente(paciente_dados)

            if not paciente:
                logger.error(
                    f"[BOTCONVERSA] Falha ao criar paciente | telefone={agendamento_data.telefone}"
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Não foi possível criar o paciente",
                )
            paciente_criado = True
            logger.info(
                f"[BOTCONVERSA] Paciente criado | paciente_id={paciente.id} | "
                f"nome={paciente.nome} | telefone={paciente.telefone}"
            )
        elif agendamento_data.nome_paciente:
            # Atualiza nome se fornecido
            logger.debug(
                f"[BOTCONVERSA] Atualizando nome do paciente | paciente_id={paciente.id} | "
                f"nome_antigo={paciente.nome} | nome_novo={agendamento_data.nome_paciente}"
            )
            paciente.nome = agendamento_data.nome_paciente
            db.commit()
            db.refresh(paciente)

        logger.debug(
            f"[BOTCONVERSA] Paciente validado | paciente_id={paciente.id} | "
            f"nome={paciente.nome} | telefone={paciente.telefone} | "
            f"paciente_criado={paciente_criado}"
        )

        # Busca médico e especialidade
        logger.debug(
            f"[BOTCONVERSA] Buscando médico | medico_id={agendamento_data.medico_id}"
        )
        medico_service = MedicoService(db)
        medico = medico_service.buscar_medico(agendamento_data.medico_id)

        if not medico:
            logger.warning(
                f"[BOTCONVERSA] Médico não encontrado | medico_id={agendamento_data.medico_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico não encontrado",
            )

        if not medico.ativo:
            logger.warning(
                f"[BOTCONVERSA] Médico inativo | medico_id={agendamento_data.medico_id} | "
                f"nome={medico.nome}"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Médico não está ativo",
            )

        # Busca especialidade
        logger.debug(
            f"[BOTCONVERSA] Buscando especialidade | especialidade_id={medico.especialidade_id}"
        )
        esp_service = EspecialidadeService(db)
        especialidade = esp_service.buscar_especialidade(medico.especialidade_id)

        if not especialidade:
            logger.warning(
                f"[BOTCONVERSA] Especialidade não encontrada | especialidade_id={medico.especialidade_id}"
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Especialidade não encontrada",
            )

        logger.debug(
            f"[BOTCONVERSA] Médico e especialidade validados | medico_id={medico.id} | "
            f"medico_nome={medico.nome} | especialidade_nome={especialidade.nome}"
        )

        # Cria agendamento
        logger.debug(
            f"[BOTCONVERSA] Criando agendamento | paciente_id={paciente.id} | "
            f"medico_id={agendamento_data.medico_id} | data_hora={agendamento_data.data_hora}"
        )
        agendamento_service = AgendamentoService(db)
        agendamento_dados = {
            "paciente_id": paciente.id,
            "medico_id": agendamento_data.medico_id,
            "data_hora": agendamento_data.data_hora,
            "duracao_minutos": agendamento_data.duracao_minutos,
            "observacoes": agendamento_data.observacoes,
        }

        agendamento = agendamento_service.criar_agendamento(agendamento_dados)

        if not agendamento:
            logger.warning(
                f"[BOTCONVERSA] Falha ao criar agendamento | paciente_id={paciente.id} | "
                f"medico_id={agendamento_data.medico_id} | data_hora={agendamento_data.data_hora} | "
                f"motivo=Horário indisponível ou validação falhou"
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível criar o agendamento. Horário pode estar indisponível.",
            )

        logger.debug(
            f"[BOTCONVERSA] Agendamento criado | agendamento_id={agendamento.id} | "
            f"status={agendamento.status.value}"
        )

        # Formata mensagem de confirmação
        logger.debug(
            f"[BOTCONVERSA] Formatando mensagem de confirmação | agendamento_id={agendamento.id}"
        )
        mensagem = formatar_mensagem_confirmacao_agendamento(
            agendamento=agendamento,
            medico=medico,
            especialidade=especialidade,
            paciente=paciente,
            hospital_name=settings.hospital_name,
            hospital_address=settings.hospital_address,
            hospital_phone=settings.hospital_phone,
        )

        logger.success(
            f"[BOTCONVERSA] Agendamento criado com sucesso via Botconversa | "
            f"agendamento_id={agendamento.id} | paciente_id={paciente.id} | "
            f"paciente_nome={paciente.nome} | medico_id={medico.id} | medico_nome={medico.nome} | "
            f"especialidade={especialidade.nome} | data_hora={agendamento.data_hora} | "
            f"paciente_criado={paciente_criado}"
        )

        return AgendamentoConfirmacaoResponse(
            agendamento_id=agendamento.id,
            mensagem=mensagem,
            agendamento=agendamento,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(
            f"[BOTCONVERSA] Erro ao criar agendamento | telefone={agendamento_data.telefone} | "
            f"medico_id={agendamento_data.medico_id} | data_hora={agendamento_data.data_hora} | "
            f"erro={str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno ao criar agendamento: {str(e)}",
        )
