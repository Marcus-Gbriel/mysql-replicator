# Sistema de Replicação de Banco de Dados MySQL

Um sistema completo e profissional para replicar estruturas e dados entre bancos de dados MySQL, ideal para sincronização entre ambientes de desenvolvimento e produção.

## 🚀 Características

- **Replicação Inteligente**: Analisa diferenças estruturais e replica apenas o necessário
- **Backups Automáticos**: Cria backups automáticos antes de modificações críticas
- **Interface CLI Intuitiva**: Interface de linha de comando fácil de usar
- **Configuração Flexível**: Suporte a múltiplos ambientes e configurações personalizadas
- **Logs Detalhados**: Sistema de logging completo para auditoria e depuração
- **Gerenciamento de Dependências**: Resolve automaticamente dependências entre tabelas

## 📁 Estrutura do Projeto

```
replicator/
├── src/                            # Código fonte organizado
│   ├── __init__.py
│   ├── core/                       # Funcionalidades principais
│   │   ├── __init__.py
│   │   └── replicator.py           # Lógica principal de replicação
│   ├── managers/                   # Gerenciadores do sistema
│   │   ├── __init__.py
│   │   ├── backup_manager.py       # Gerenciamento de backups
│   │   ├── config_manager.py       # Gerenciamento de configurações
│   │   ├── database_manager.py     # Gerenciamento de conexões de banco
│   │   └── structure_analyzer.py   # Análise de diferenças estruturais
│   ├── utils/                      # Utilitários e ferramentas
│   │   ├── __init__.py
│   │   └── logger.py               # Sistema de logging
│   └── interface/                  # Interfaces de usuário
│       ├── __init__.py
│       └── cli_interface.py        # Interface de linha de comando
├── main.py                         # Ponto de entrada principal
├── config.json                     # Configuração principal (não versionado)
├── config_example.json             # Exemplo de configuração
├── requirements.txt                # Dependências Python
├── .gitignore                      # Arquivos ignorados pelo Git
├── README.md                       # Esta documentação
├── PROJECT_STRUCTURE.md            # Estrutura detalhada do projeto
├── REPLICATION_GUIDE.md            # Guia de uso da replicação
├── TECHNICAL_DOCS.md               # Documentação técnica
├── backups/                        # Backups criados pelo sistema
└── logs/                           # Logs de execução
```

## 🔧 Instalação

1. **Clone o repositório**:

   ```bash
   git clone <url-do-repositório>
   cd replicator
   ```

2. **Instale as dependências**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o sistema**:

   ```bash
   cp config_example.json config.json
   # Edite config.json com suas configurações de banco
   ```

## ⚙️ Configuração

Edite o arquivo `config.json` com suas configurações:

```json
{
  "database": {
    "development": {
      "server": "localhost",
      "database": "db_desenvolvimento",
      "user": "usuario_dev",
      "password": "senha_dev"
    },
    "production": {
      "server": "servidor_producao",
      "database": "db_producao",
      "user": "usuario_prod",
      "password": "senha_prod"
    },
    "maintain": [
      "tabela_importante",
      "tabela_dados_criticos"
    ]
  }
}
```

## 🚀 Uso

### Execução Principal

```bash
python main.py
```

### Menu Principal

O sistema oferece um menu interativo com as seguintes opções:

1. **Analisar Replicação** - Analisa diferenças entre os bancos
2. **Backups** - Gerencia backups do sistema
3. **Replicação** - Executa replicação completa
4. **Configuração** - Gerencia configurações do sistema
5. **Testar Conexões** - Testa conectividade com os bancos

### Tipos de Replicação

- **Estrutura**: Replica apenas a estrutura das tabelas (DDL)
- **Dados**: Replica dados das tabelas configuradas em "maintain"
- **Completa**: Replica estrutura de todas as tabelas + dados das tabelas "maintain"

## 📊 Funcionalidades Detalhadas

### 🔍 Análise de Diferenças

- Compara estruturas de tabelas
- Identifica diferenças em colunas, índices e chaves estrangeiras
- Gera plano de replicação otimizado
- Resolve dependências entre tabelas

### 💾 Sistema de Backup

- Backup automático antes de modificações
- Suporte a backup completo ou por tabelas específicas
- Armazenamento organizado por data/hora
- Limpeza automática de backups antigos

### 🔧 Gerenciamento de Configuração

- Múltiplos ambientes (desenvolvimento, produção, etc.)
- Configuração de tabelas para manutenção de dados
- Interface para edição de configurações
- Validação de configurações

## 🛠️ Arquitetura

### Padrões Utilizados

- **Separation of Concerns**: Cada módulo tem responsabilidade específica
- **Dependency Injection**: Dependências injetadas via construtores
- **Context Managers**: Gerenciamento automático de recursos
- **Error Handling**: Tratamento robusto de erros

### Principais Classes

- **Replicator**: Lógica principal de replicação
- **DatabaseManager**: Gerenciamento de conexões e operações de banco
- **StructureAnalyzer**: Análise de diferenças estruturais
- **BackupManager**: Gerenciamento de backups
- **ConfigManager**: Gerenciamento de configurações
- **Logger**: Sistema de logging
- **CLIInterface**: Interface de linha de comando

## 🔒 Segurança

- Backups automáticos antes de modificações
- Validação de configurações
- Logs detalhados para auditoria
- Tratamento de transações para consistência

## 🐛 Resolução de Problemas

### Problemas Comuns

1. **Erro de Conexão**: Verifique as configurações de banco em `config.json`
2. **Erro de Permissão**: Certifique-se de que o usuário tem permissões adequadas
3. **Erro de Dependência**: O sistema resolve automaticamente dependências entre tabelas

### Logs

Os logs são salvos em `logs/` e contêm informações detalhadas sobre:

- Operações realizadas
- Erros encontrados
- Estatísticas de replicação
- Tempos de execução

## 📈 Melhorias Futuras

- [ ] Interface web
- [ ] Suporte a outros SGBDs
- [ ] Replicação incremental
- [ ] Notificações por email
- [ ] Métricas de performance
- [ ] Configuração via linha de comando

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Faça commit das suas alterações
4. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:

- Abra uma issue no GitHub
- Consulte a documentação técnica em `TECHNICAL_DOCS.md`
- Veja o guia de replicação em `REPLICATION_GUIDE.md`
