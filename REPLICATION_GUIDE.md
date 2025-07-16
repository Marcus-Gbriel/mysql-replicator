# Funcionalidade de Replicação - Estrutura vs Dados

## Resumo das Mudanças

O sistema foi atualizado para suportar dois tipos de replicação:

### 1. **Replicação de Estrutura** (Todas as Tabelas)
- **Escopo**: Todas as tabelas do banco de desenvolvimento
- **Operações**: CREATE TABLE, ALTER TABLE, índices, chaves estrangeiras
- **Objetivo**: Manter estrutura idêntica entre desenvolvimento e produção

### 2. **Replicação de Dados** (Apenas Tabelas Maintain)
- **Escopo**: Apenas tabelas listadas em `config.json` → `database.maintain`
- **Operações**: TRUNCATE + INSERT de todos os dados
- **Objetivo**: Sincronizar dados de tabelas de configuração/master

## Comportamento Atual

### Análise de Replicação
```
1. Analisa TODAS as tabelas do desenvolvimento
2. Identifica diferenças estruturais em todas as tabelas
3. Identifica diferenças de dados apenas em tabelas maintain
4. Mostra prefixo [MAINTAIN] ou [STRUCTURE] para cada tabela
```

### Execução da Replicação
```
1. Cria backup de todas as tabelas da produção
2. Replica estrutura de TODAS as tabelas do desenvolvimento
3. Replica dados apenas das tabelas em maintain
4. Registra logs detalhados de todas as operações
```

## Exemplo de Uso

### Configuração Atual
```json
{
    "database": {
        "maintain": [
            "agencies",
            "areas", 
            "permissions",
            "procedures",
            "steps"
        ]
    }
}
```

### Resultado da Replicação
- **Estrutura**: Todas as 29 tabelas do desenvolvimento serão replicadas
- **Dados**: Apenas 5 tabelas (agencies, areas, permissions, procedures, steps) terão dados replicados

## Interface CLI

### Tela de Análise
```
Total de tabelas no desenvolvimento: 29
Tabelas para replicar estrutura: 29 (todas)
Tabelas para replicar dados: 5 (agencies, areas, permissions, procedures, steps)

Detalhes das Diferenças:
❌ [MAINTAIN] agencies: Não existe no destino
❌ [STRUCTURE] users: Não existe no destino  
❌ [STRUCTURE] logs: Não existe no destino
...

Legenda:
[MAINTAIN] = Estrutura + Dados serão replicados
[STRUCTURE] = Apenas estrutura será replicada
```

### Tela de Replicação
```
Total de tabelas para replicar estrutura: 29
Tabelas para replicar dados: 5 (agencies, areas, permissions, procedures, steps)

Estrutura será replicada para:
  • agencies
  • areas
  • logs
  • permissions
  • procedures
  • steps
  • users
  • ...

Dados serão replicados para:
  • agencies
  • areas
  • permissions
  • procedures
  • steps
```

## Fluxo de Operações

### 1. Backup
```
- Cria backup de TODAS as tabelas da produção
- Inclui estrutura e dados existentes
- Usado para rollback se necessário
```

### 2. Replicação de Estrutura
```
Para cada tabela do desenvolvimento:
  1. Verifica se existe na produção
  2. Se não existir: CREATE TABLE
  3. Se existir: Compara estruturas
  4. Aplica ALTER TABLE se necessário
  5. Ajusta índices e chaves estrangeiras
```

### 3. Replicação de Dados
```
Para cada tabela em maintain:
  1. Verifica se existe em ambos os bancos
  2. TRUNCATE da tabela na produção
  3. INSERT de todos os dados do desenvolvimento
  4. Valida contagem de registros
```

## Vantagens da Nova Abordagem

### ✅ **Estrutura Completa**
- Todas as tabelas ficam disponíveis na produção
- Estrutura idêntica entre ambientes
- Facilita deploy de novas funcionalidades

### ✅ **Dados Controlados**
- Apenas tabelas críticas têm dados replicados
- Evita sobrescrever dados de produção
- Controle granular sobre sincronização

### ✅ **Flexibilidade**
- Pode adicionar/remover tabelas do maintain
- Estrutura sempre atualizada
- Dados sob controle

### ✅ **Segurança**
- Backup automático antes de operações
- Logs detalhados de todas as ações
- Confirmação antes de executar

## Casos de Uso

### 1. **Primeira Implantação**
```
- Produção vazia
- Replica estrutura de todas as tabelas
- Replica dados apenas das tabelas master
- Resultado: Estrutura completa com dados controlados
```

### 2. **Atualização de Estrutura**
```
- Produção com dados
- Detecta novas tabelas/colunas
- Aplica ALTER TABLE necessários
- Mantém dados de produção intactos
- Atualiza apenas dados das tabelas maintain
```

### 3. **Sincronização de Dados Master**
```
- Estrutura já sincronizada
- Apenas dados das tabelas maintain são diferentes
- Trunca e replica dados master
- Mantém dados transacionais intactos
```

## Configuração

### Adicionar Tabela ao Maintain
```
1. Menu → Configuração → Gerenciar Tabelas de Manutenção
2. Adicionar Tabela → Digite nome da tabela
3. Dados da tabela serão replicados na próxima execução
```

### Remover Tabela do Maintain
```
1. Menu → Configuração → Gerenciar Tabelas de Manutenção
2. Escolher tabela da lista
3. Apenas estrutura será replicada (dados preservados)
```

## Logs

### Exemplo de Log
```
[INFO] Iniciando replicação completa
[INFO] Total de tabelas para replicar estrutura: 29
[INFO] Tabelas para replicar dados: ['agencies', 'areas', 'permissions', 'procedures', 'steps']
[INFO] Criando backup antes da replicação
[SUCCESS] Backup criado com sucesso: backup_production_20250716_165400
[INFO] Replicando estrutura da tabela: agencies
[SUCCESS] Tabela agencies criada no destino
[INFO] Replicando estrutura da tabela: users
[SUCCESS] Tabela users criada no destino
[INFO] Replicando dados da tabela: agencies
[SUCCESS] Tabela agencies: 13 registros copiados, 13 registros no destino
[SUCCESS] Replicação completa concluída
```

Este novo comportamento atende perfeitamente ao seu cenário:
- **Estrutura completa**: Todas as tabelas ficam disponíveis
- **Dados controlados**: Apenas tabelas críticas têm dados sincronizados
- **Flexibilidade**: Pode ajustar quais tabelas têm dados replicados
- **Segurança**: Backup automático e logs detalhados
