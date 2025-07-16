# Sistema de Replicação de Banco de Dados MySQL

Sistema completo para replicação de estrutura e dados entre bancos de dados MySQL, desenvolvido especificamente para sincronização entre ambientes de desenvolvimento (homologação) e produção.

## Características

- **Replicação Completa**: Replica estrutura de tabelas, índices, chaves estrangeiras e dados
- **Análise de Diferenças**: Compara estruturas entre bancos e identifica diferenças
- **Backup Automático**: Cria backups antes de realizar modificações
- **Interface CLI**: Interface de linha de comando amigável
- **Logs Detalhados**: Sistema de logging completo
- **Configuração Flexível**: Gerenciamento de configurações via arquivo JSON

## Instalação

1. **Pré-requisitos**:
   - Python 3.7+
   - MySQL Server
   - Acesso aos bancos de dados de origem e destino

2. **Instalação de dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuração**:
   - Edite o arquivo `config.json` com suas configurações de banco de dados
   - Configure as tabelas que devem ser mantidas na seção `maintain`

## Configuração

O arquivo `config.json` deve conter:

```json
{
    "version": "1.0",
    "settings": {},
    "database": {
        "production": {
            "server": "servidor-producao",
            "database": "banco_producao",
            "user": "usuario",
            "password": "senha"
        },
        "development": {
            "server": "servidor-desenvolvimento",
            "database": "banco_desenvolvimento",
            "user": "usuario",
            "password": "senha"
        },
        "maintain": [
            "tabela1",
            "tabela2",
            "tabela3"
        ]
    }
}
```

## Uso

Execute o sistema com:

```bash
python main.py
```

### Menu Principal

1. **Analisar Replicação**: Analisa diferenças entre bancos e oferece opção de replicação
2. **Backups**: Gerencia backups do sistema
3. **Replicação**: Executa replicação completa
4. **Configuração**: Gerencia configurações do sistema
5. **Testar Conexões**: Testa conectividade com os bancos

### Funcionalidades Detalhadas

#### 1. Análise de Replicação
- Compara estruturas de tabelas entre origem e destino
- Identifica diferenças em colunas, tipos, chaves estrangeiras e índices
- Mostra contagem de registros em cada tabela
- Oferece opção de replicação após análise

#### 2. Backups
- **Listar Backups**: Mostra todos os backups disponíveis
- **Criar Backup**: Cria backup de ambiente específico
- **Remover Backup**: Remove backup selecionado
- **Limpar Backups Antigos**: Mantém apenas os backups mais recentes

#### 3. Replicação
- Replicação completa de estrutura e dados
- Backup automático antes da replicação
- Replicação apenas das tabelas configuradas em `maintain`
- Garante ordem idêntica das colunas

#### 4. Configuração
- **Configurar Banco de Dados**: Edita configurações de conexão
- **Gerenciar Tabelas de Manutenção**: Adiciona/remove tabelas da lista `maintain`
- **Visualizar Configuração**: Mostra configuração atual

## Estrutura do Projeto

```
replicator/
├── main.py                 # Arquivo principal
├── cli_interface.py        # Interface CLI
├── config_manager.py       # Gerenciador de configurações
├── database_manager.py     # Gerenciador de banco de dados
├── structure_analyzer.py   # Analisador de estruturas
├── replicator.py          # Lógica de replicação
├── backup_manager.py      # Gerenciador de backups
├── logger.py              # Sistema de logging
├── config.json            # Configurações
├── requirements.txt       # Dependências
└── README.md             # Documentação
```

## Funcionalidades Técnicas

### Replicação de Estrutura
- Cria tabelas inexistentes no destino
- Adiciona/remove colunas conforme necessário
- Modifica tipos de dados
- Ajusta ordem das colunas (recria tabela se necessário)
- Gerencia chaves estrangeiras
- Sincroniza índices

### Replicação de Dados
- Trunca tabelas no destino antes da cópia
- Copia todos os dados das tabelas em `maintain`
- Inserção em lotes para melhor performance
- Tratamento de caracteres especiais

### Sistema de Backup
- Backup de estrutura (CREATE TABLE)
- Backup de dados (INSERT statements)
- Metadados do backup
- Limpeza automática de backups antigos

### Logging
- Logs coloridos no console
- Logs detalhados em arquivo
- Diferentes níveis de log (INFO, WARNING, ERROR, CRITICAL)
- Timestamps automáticos

## Segurança

- Backups automáticos antes de modificações
- Transações para operações críticas
- Verificação de conexões antes de operações
- Confirmação para operações destrutivas

## Tratamento de Erros

- Verificação de conectividade
- Rollback em caso de erro
- Logs detalhados de erros
- Validação de configurações

## Limitações

- Suporte apenas para MySQL
- Não há opção de restaurar backups automaticamente
- Replicação sempre da development para production
- Tabelas devem existir na origem para serem replicadas

## Suporte

Para problemas ou dúvidas, verifique os logs gerados na pasta `logs/` ou consulte a documentação do código.

## Licença

Sistema desenvolvido para uso interno.
