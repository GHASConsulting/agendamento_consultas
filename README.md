# 🏥 Sistema de Agendamento de Consultas - API REST

API completa para agendamento de consultas médicas via WhatsApp, integrada com Botconversa para automação completa do processo de agendamento.

## 🚀 **Funcionalidades Principais**

- ✅ **CRUD Completo**: Gestão de pacientes, médicos, especialidades e agendamentos
- 📅 **Validação de Disponibilidade**: Verificação automática de horários disponíveis
- 🔄 **Reagendamento e Cancelamento**: Gestão completa do ciclo de vida dos agendamentos
- 🤖 **Integração Botconversa**: Agendamento interativo via WhatsApp
- 📊 **API REST**: Endpoints RESTful completos e documentados
- 🐳 **Docker Ready**: Containerização completa com suporte a Oracle, PostgreSQL e Firebird

## 🛠️ **Tecnologias**

- **Backend**: FastAPI + Python 3.11
- **Banco**: Suporte a Oracle, PostgreSQL e Firebird
- **ORM**: SQLAlchemy
- **Validação**: Pydantic
- **Containerização**: Docker + Docker Compose
- **Integração**: Botconversa API

## 📋 **Modelos de Dados**

- **Paciente**: Informações do paciente (nome, telefone, email, CPF)
- **Médico**: Dados do médico (nome, CRM, especialidade)
- **Especialidade**: Especialidades médicas disponíveis
- **Disponibilidade**: Horários disponíveis de cada médico
- **Agendamento**: Registro completo de agendamentos

## 🐳 **INSTALAÇÃO COM DOCKER (RECOMENDADA)**

### **📋 PRÉ-REQUISITOS**

- ✅ Docker instalado e rodando
- ✅ Docker Compose disponível
- ✅ Git instalado

### **🚀 INSTALAÇÃO RÁPIDA**

```bash
# 1. Clone o repositório
git clone <seu-repositorio>
cd agendamento_consultas

# 2. Configure as variáveis de ambiente
cp env.example .env
# Edite o .env com suas configurações

# 3. Inicie com PostgreSQL
docker-compose --profile postgresql up -d

# 4. Verifique se está funcionando
curl http://localhost:8000/health
```

### **📝 CONFIGURAÇÃO DO .env**

```bash
# Banco de dados
DOCKER_DATABASE_TYPE=postgresql  # oracle, postgresql, firebird

# Configurações de agendamento
MIN_ADVANCE_BOOKING_HOURS=24      # Antecedência mínima (horas)
MAX_ADVANCE_BOOKING_DAYS=90       # Antecedência máxima (dias)
DEFAULT_CONSULTATION_DURATION_MINUTES=30
CONSULTATION_INTERVAL_MINUTES=30

# Botconversa (opcional)
BOTCONVERSA_API_KEY=sua_api_key
BOTCONVERSA_WEBHOOK_SECRET=seu_secret
```

## 📚 **ENDPOINTS DA API**

### **Agendamentos**

- `POST /api/v1/agendamentos` - Criar novo agendamento
- `GET /api/v1/agendamentos` - Listar agendamentos (com filtros)
- `GET /api/v1/agendamentos/{id}` - Buscar agendamento específico
- `PUT /api/v1/agendamentos/{id}` - Atualizar agendamento
- `POST /api/v1/agendamentos/{id}/reagendar` - Reagendar
- `POST /api/v1/agendamentos/{id}/cancelar` - Cancelar
- `POST /api/v1/agendamentos/{id}/confirmar` - Confirmar

### **Pacientes**

- `POST /api/v1/pacientes` - Criar paciente
- `GET /api/v1/pacientes` - Listar pacientes
- `GET /api/v1/pacientes/{id}` - Buscar paciente
- `PUT /api/v1/pacientes/{id}` - Atualizar paciente
- `DELETE /api/v1/pacientes/{id}` - Deletar paciente

### **Médicos**

- `POST /api/v1/medicos` - Criar médico
- `GET /api/v1/medicos` - Listar médicos (com filtros)
- `GET /api/v1/medicos/{id}` - Buscar médico
- `PUT /api/v1/medicos/{id}` - Atualizar médico
- `POST /api/v1/medicos/especialidades` - Criar especialidade
- `GET /api/v1/medicos/especialidades` - Listar especialidades

### **Disponibilidade**

- `GET /api/v1/disponibilidade/horarios` - Buscar horários disponíveis

## 📖 **EXEMPLOS DE USO**

### **Criar um Agendamento**

```bash
curl -X POST "http://localhost:8000/api/v1/agendamentos" \
  -H "Content-Type: application/json" \
  -d '{
    "paciente_id": 1,
    "medico_id": 1,
    "data_hora": "2024-12-25T10:00:00",
    "duracao_minutos": 30,
    "observacoes": "Primeira consulta"
  }'
```

### **Buscar Horários Disponíveis**

```bash
curl "http://localhost:8000/api/v1/disponibilidade/horarios?medico_id=1&data_inicio=2024-12-20T00:00:00&data_fim=2024-12-30T23:59:59"
```

### **Reagendar**

```bash
curl -X POST "http://localhost:8000/api/v1/agendamentos/1/reagendar" \
  -H "Content-Type: application/json" \
  -d '{
    "nova_data_hora": "2024-12-26T14:00:00",
    "motivo": "Conflito de horário"
  }'
```

## 🗄️ **ESTRUTURA DO BANCO DE DADOS**

O sistema cria automaticamente as seguintes tabelas:

- `pacientes` - Cadastro de pacientes
- `medicos` - Cadastro de médicos
- `especialidades` - Especialidades médicas
- `disponibilidades` - Horários disponíveis dos médicos
- `agendamentos` - Registros de agendamentos

## 🔧 **VALIDAÇÕES IMPLEMENTADAS**

- ✅ Verificação de disponibilidade do médico
- ✅ Validação de antecedência mínima e máxima
- ✅ Detecção de conflitos de horário
- ✅ Verificação de médico ativo
- ✅ Validação de período de disponibilidade

## 📖 **DOCUMENTAÇÃO COMPLETA**

Acesse a documentação interativa da API em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🚀 **DESENVOLVIMENTO**

### **Instalação Local**

```bash
# Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Configurar .env
cp env.example .env

# Executar aplicação
python -m app.main
```

## 📝 **NOTAS**

- O sistema valida automaticamente conflitos de horário
- Agendamentos podem ser reagendados ou cancelados
- A API suporta múltiplos bancos de dados (Oracle, PostgreSQL, Firebird)
- Integração com Botconversa para agendamento via WhatsApp (a ser implementada)

## 📄 **LICENÇA**

Este projeto é propriedade do hospital/clínica que o utiliza.

