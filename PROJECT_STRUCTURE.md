# Estrutura do Sistema de Replicação

## 📁 Estrutura Organizada

### 🔧 Arquivo Principal
- `main.py` - Ponto de entrada principal do sistema

### 📂 Diretório src/
Código fonte organizado em módulos lógicos:

#### 🎯 src/core/
Funcionalidades principais do sistema:
- `replicator.py` - Lógica principal de replicação

#### 🛠️ src/managers/
Gerenciadores especializados:
- `backup_manager.py` - Gerenciamento de backups
- `config_manager.py` - Gerenciamento de configurações
- `database_manager.py` - Gerenciamento de conexões e operações de banco
- `structure_analyzer.py` - Análise de diferenças estruturais

#### 🔧 src/utils/
Utilitários e ferramentas auxiliares:
- `logger.py` - Sistema de logging

#### 🖥️ src/interface/
Interfaces de usuário:
- `cli_interface.py` - Interface de linha de comando

### 📋 Arquivos de Configuração
- `config.json` - Configuração principal (sensível, não versionar)
- `config_example.json` - Exemplo de configuração
- `requirements.txt` - Dependências Python
- `.gitignore` - Arquivos ignorados pelo Git

### 📚 Documentação
- `README.md` - Documentação principal
- `PROJECT_STRUCTURE.md` - Este arquivo
- `REPLICATION_GUIDE.md` - Guia de uso da replicação
- `TECHNICAL_DOCS.md` - Documentação técnica

### 🗂️ Diretórios de Trabalho
- `backups/` - Backups criados pelo sistema
- `logs/` - Logs de execução
- `__pycache__/` - Cache Python (ignorado pelo Git)

## 🔗 Dependências entre Módulos

### Hierarquia de Imports
```
main.py
└── src.interface.cli_interface
    ├── src.managers.config_manager
    ├── src.managers.database_manager
    ├── src.managers.backup_manager
    ├── src.managers.structure_analyzer
    ├── src.core.replicator
    └── src.utils.logger
```

### Responsabilidades

#### 🎯 Core Module
- **replicator.py**: Orquestra todo o processo de replicação, coordenando outros módulos

#### 🛠️ Managers Module
- **config_manager.py**: Carrega e gerencia configurações do sistema
- **database_manager.py**: Abstrai operações de banco de dados
- **backup_manager.py**: Cria e gerencia backups
- **structure_analyzer.py**: Analisa diferenças entre estruturas de banco

#### 🔧 Utils Module
- **logger.py**: Sistema de logging centralizado

#### 🖥️ Interface Module
- **cli_interface.py**: Interface de linha de comando interativa

## 📊 Benefícios da Organização

### ✅ Vantagens
1. **Separação de Responsabilidades**: Cada módulo tem uma função específica
2. **Manutenibilidade**: Código mais fácil de manter e modificar
3. **Testabilidade**: Módulos isolados são mais fáceis de testar
4. **Reutilização**: Componentes podem ser reutilizados em outros projetos
5. **Escalabilidade**: Estrutura permite fácil adição de novos recursos

### � Padrões Utilizados
- **Modularização**: Código dividido em módulos lógicos
- **Injeção de Dependências**: Dependências passadas via construtor
- **Separation of Concerns**: Cada classe tem responsabilidade única
- **Interface Segregation**: Interfaces específicas para cada necessidade

## 🚀 Como Adicionar Novos Recursos

### Adicionando um Novo Manager
1. Crie o arquivo em `src/managers/`
2. Implemente a classe seguindo o padrão existente
3. Adicione import em `src/managers/__init__.py`
4. Importe onde necessário

### Adicionando Utilitários
1. Crie o arquivo em `src/utils/`
2. Implemente as funções/classes
3. Adicione import em `src/utils/__init__.py`

### Adicionando Nova Interface
1. Crie o arquivo em `src/interface/`
2. Implemente a interface
3. Integre com o sistema existente

## 🔧 Configuração de Desenvolvimento

### Estrutura de Imports
Use imports relativos dentro do pacote `src`:
```python
# Exemplo em src/core/replicator.py
from ..managers.database_manager import DatabaseManager
from ..utils.logger import Logger
```

### Convenções de Nomenclatura
- **Arquivos**: snake_case (ex: `database_manager.py`)
- **Classes**: PascalCase (ex: `DatabaseManager`)
- **Métodos/Funções**: snake_case (ex: `get_connection()`)
- **Constantes**: UPPER_CASE (ex: `DEFAULT_PORT`)

## 🧪 Testes

### Estrutura de Testes (Futura)
```
tests/
├── __init__.py
├── test_core/
│   └── test_replicator.py
├── test_managers/
│   ├── test_backup_manager.py
│   ├── test_config_manager.py
│   ├── test_database_manager.py
│   └── test_structure_analyzer.py
├── test_utils/
│   └── test_logger.py
└── test_interface/
    └── test_cli_interface.py
```

Esta estrutura organizada facilita a manutenção, desenvolvimento e expansão do sistema de replicação de banco de dados.
- Cache Python (`__pycache__/`)
- Arquivos temporários
- Configurações sensíveis
- Logs antigos

## Uso

```bash
# Executar sistema
python main.py

# Instalar dependências
pip install -r requirements.txt
```

## Funcionalidades Implementadas

✅ **Replicação de Estrutura com Posicionamento Correto**
- Detecta colunas faltantes/extras
- Adiciona colunas na posição correta (AFTER)
- Trata valores DEFAULT especiais (current_timestamp)
- Gerencia chaves estrangeiras sem quebrar dependências

✅ **Replicação de Dados Seletiva**
- Tabelas "maintain": estrutura + dados
- Outras tabelas: apenas estrutura
- Limpeza segura com FK constraints

✅ **Sistema de Backup Automático**
- Backup antes de alterações
- Metadados de backup
- Recuperação facilitada

✅ **Interface CLI Completa**
- Análise de diferenças
- Replicação estrutura/dados
- Gerenciamento de backups
- Configurações
- Teste de conexões

## Sistema em Produção - Pronto para Uso! 🚀
