# Documentação Técnica - Sistema de Replicação

## Arquitetura do Sistema

### Componentes Principais

1. **DatabaseManager** - Gerencia conexões e operações com MySQL
2. **StructureAnalyzer** - Analisa diferenças entre estruturas
3. **Replicator** - Executa a replicação de dados e estruturas
4. **BackupManager** - Gerencia backups automáticos
5. **ConfigManager** - Gerencia configurações do sistema
6. **CLIInterface** - Interface de linha de comando
7. **Logger** - Sistema de logging

### Fluxo de Replicação

1. **Análise**: Compara estruturas entre origem e destino
2. **Backup**: Cria backup automático da produção
3. **Estrutura**: Replica estrutura das tabelas
4. **Dados**: Replica dados das tabelas configuradas
5. **Verificação**: Valida a replicação

### Processo de Replicação de Estrutura

```
1. Verificar existência da tabela
2. Se não existir no destino: Criar tabela
3. Se existir: Comparar estruturas
4. Identificar diferenças:
   - Colunas faltantes/extras
   - Tipos de dados diferentes
   - Ordem das colunas
   - Chaves estrangeiras
   - Índices
5. Aplicar correções necessárias
6. Recriar tabela se necessário (ordem de colunas)
```

### Processo de Replicação de Dados

```
1. Verificar se tabela existe em ambos os bancos
2. Obter estrutura da tabela
3. Truncar tabela de destino
4. Obter dados da origem
5. Inserir dados em lotes no destino
6. Verificar contagem de registros
```

## Configuração Avançada

### Configurações Adicionais

```json
{
    "settings": {
        "backup_retention_days": 30,    // Dias para manter backups
        "max_backups": 50,              // Máximo de backups
        "batch_size": 1000,             // Tamanho do lote para inserção
        "log_level": "INFO",            // Nível de log
        "connection_timeout": 30,       // Timeout de conexão
        "retry_attempts": 3             // Tentativas de retry
    }
}
```

### Conexão com Banco

```python
# Exemplo de configuração de conexão
connection_config = {
    'host': 'servidor',
    'database': 'banco',
    'user': 'usuario',
    'password': 'senha',
    'charset': 'utf8mb4',
    'autocommit': False,
    'time_zone': '+00:00'
}
```

## Tratamento de Erros

### Tipos de Erro

1. **Erro de Conexão**: Falha na conexão com banco
2. **Erro de Estrutura**: Problema na alteração de estrutura
3. **Erro de Dados**: Problema na inserção/atualização de dados
4. **Erro de Backup**: Falha na criação de backup
5. **Erro de Configuração**: Problema na configuração

### Estratégias de Recuperação

1. **Retry Automático**: Para erros temporários
2. **Rollback**: Para erros críticos
3. **Backup Restore**: Para reverter alterações
4. **Log Detalhado**: Para diagnóstico

## Otimizações

### Performance

1. **Inserção em Lotes**: Reduz overhead de transações
2. **Índices Temporários**: Remove índices durante inserção
3. **Transações Grandes**: Agrupa operações
4. **Conexões Persistentes**: Reutiliza conexões

### Memória

1. **Streaming de Dados**: Não carrega todos os dados em memória
2. **Limpeza de Objetos**: Libera memória após uso
3. **Compressão de Backup**: Reduz tamanho dos backups

## Segurança

### Práticas Implementadas

1. **Backup Automático**: Sempre antes de modificações
2. **Validação de Entrada**: Sanitização de dados
3. **Transações**: Garantia de consistência
4. **Logs Auditoria**: Rastreamento de operações
5. **Confirmação de Operações**: Evita execução acidental

### Recomendações

1. **Credenciais Seguras**: Use senhas fortes
2. **Permissões Limitadas**: Usuário com permissões mínimas
3. **Backup Externo**: Mantenha backups em local seguro
4. **Monitoramento**: Monitore logs regularmente

## Monitoramento

### Métricas Importantes

1. **Tempo de Replicação**: Monitore performance
2. **Tamanho dos Dados**: Acompanhe crescimento
3. **Erros**: Monitore falhas
4. **Uso de Espaço**: Verifique storage
5. **Conexões**: Monitore pool de conexões

### Logs

```
logs/
├── replicator_YYYYMMDD_HHMMSS.log
├── backup_history.log
├── error_summary.log
└── performance_metrics.log
```

## Resolução de Problemas

### Problemas Comuns

1. **Erro de Conexão**
   - Verificar credenciais
   - Testar conectividade de rede
   - Verificar firewall

2. **Erro de Estrutura**
   - Verificar permissões de ALTER TABLE
   - Validar integridade referencial
   - Verificar constraints

3. **Erro de Dados**
   - Verificar encoding
   - Validar tipos de dados
   - Verificar constraints

4. **Erro de Backup**
   - Verificar espaço em disco
   - Verificar permissões de escrita
   - Validar estrutura de diretórios

### Comandos de Diagnóstico

```bash
# Testar conexões
python test_system.py

# Verificar logs
tail -f logs/replicator_*.log

# Verificar configuração
python -c "from config_manager import ConfigManager; print(ConfigManager().config)"

# Listar tabelas
python -c "from database_manager import DatabaseManager; from config_manager import ConfigManager; print(DatabaseManager(ConfigManager().get_database_config('development')).get_all_tables())"
```

## Manutenção

### Rotinas Recomendadas

1. **Diária**
   - Verificar logs de erro
   - Monitorar espaço em disco
   - Validar backups

2. **Semanal**
   - Limpar logs antigos
   - Verificar performance
   - Testar conectividade

3. **Mensal**
   - Atualizar documentação
   - Revisar configurações
   - Backup completo

### Atualizações

1. **Backup Completo**: Antes de atualizar
2. **Teste em Ambiente**: Validar mudanças
3. **Documentação**: Atualizar após mudanças
4. **Rollback Plan**: Ter plano de reversão
