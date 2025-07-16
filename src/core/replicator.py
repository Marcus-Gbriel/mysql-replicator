from typing import List, Dict, Any
from ..managers.database_manager import DatabaseManager
from ..managers.structure_analyzer import StructureAnalyzer
from ..managers.backup_manager import BackupManager
from ..utils.logger import Logger

class Replicator:
    def __init__(self, source_db: DatabaseManager, target_db: DatabaseManager, 
                 backup_manager: BackupManager, logger: Logger):
        self.source_db = source_db
        self.target_db = target_db
        self.backup_manager = backup_manager
        self.logger = logger
        self.analyzer = StructureAnalyzer(source_db, target_db, logger)
    
    def replicate_structure(self, tables: List[str], maintain_tables: List[str] = None, create_backup: bool = True) -> bool:
        """Replica estrutura das tabelas"""
        if maintain_tables is None:
            maintain_tables = []
            
        try:
            self.logger.info("Iniciando replicação de estrutura")
            
            # Criar backup se solicitado
            if create_backup:
                self.logger.info("Criando backup antes da replicação")
                self.backup_manager.create_backup(self.target_db, "production", tables)
            
            # Obter plano de replicação
            plan = self.analyzer.get_replication_plan(tables, maintain_tables)
            
            # Separar tabelas para criar primeiro (sem dependências) e depois (com dependências)
            tables_to_create = []
            tables_to_alter = []
            
            for step in plan:
                table_name = step['table']
                
                for action in step['actions']:
                    if action['type'] == 'create_table':
                        tables_to_create.append(table_name)
                    elif action['type'] in ['alter_table', 'update_foreign_keys', 'update_indexes']:
                        tables_to_alter.append((table_name, action))
            
            # Ordenar tabelas por dependência
            if tables_to_create:
                tables_to_create = self._sort_tables_by_dependency(tables_to_create)
            
            # Criar tabelas primeiro (pode haver erro de chave estrangeira, mas será tratado)
            self.logger.info("Criando tabelas...")
            for table_name in tables_to_create:
                self.logger.info(f"Criando tabela: {table_name}")
                self._create_table(table_name)
            
            # Aplicar alterações estruturais
            self.logger.info("Aplicando alterações estruturais...")
            for table_name, action in tables_to_alter:
                self.logger.info(f"Alterando estrutura da tabela: {table_name}")
                
                if action['type'] == 'alter_table':
                    self._alter_table(table_name, action['differences'])
                elif action['type'] == 'update_foreign_keys':
                    self._update_foreign_keys(table_name, action['differences'])
                elif action['type'] == 'update_indexes':
                    self._update_indexes(table_name, action['differences'])
            
            # Adicionar chaves estrangeiras que podem ter falhado na criação
            self.logger.info("Adicionando chaves estrangeiras pendentes...")
            self._add_missing_foreign_keys(tables_to_create)
            
            self.logger.success("Replicação de estrutura concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na replicação de estrutura: {e}")
            return False
    
    def replicate_data(self, tables: List[str]) -> bool:
        """Replica dados das tabelas"""
        try:
            self.logger.info("Iniciando replicação de dados")
            
            for table_name in tables:
                if not self.source_db.table_exists(table_name):
                    self.logger.warning(f"Tabela {table_name} não existe na origem, pulando")
                    continue
                
                if not self.target_db.table_exists(table_name):
                    self.logger.warning(f"Tabela {table_name} não existe no destino, pulando")
                    continue
                
                self.logger.info(f"Replicando dados da tabela: {table_name}")
                
                # Obter estrutura da tabela
                structure = self.source_db.get_table_structure(table_name)
                columns = [col['Field'] for col in structure]
                
                if not columns:
                    self.logger.warning(f"Tabela {table_name} não possui colunas")
                    continue
                
                # Limpar tabela de destino
                self.logger.info(f"Limpando tabela {table_name} no destino")
                if not self.target_db.truncate_table(table_name):
                    self.logger.error(f"Erro ao limpar tabela {table_name}")
                    return False
                
                # Copiar dados
                self.logger.info(f"Copiando dados da tabela {table_name}")
                source_data = self.source_db.get_table_data(table_name)
                
                if source_data:
                    if not self._insert_data(table_name, columns, source_data):
                        self.logger.error(f"Erro ao inserir dados na tabela {table_name}")
                        return False
                
                source_count = len(source_data)
                target_count = self.target_db.get_table_count(table_name)
                
                self.logger.success(f"Tabela {table_name}: {source_count} registros copiados, {target_count} registros no destino")
            
            self.logger.success("Replicação de dados concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na replicação de dados: {e}")
            return False
    
    def full_replication(self, all_tables: List[str], maintain_tables: List[str], create_backup: bool = True) -> bool:
        """Replicação completa (estrutura + dados)"""
        try:
            self.logger.info("Iniciando replicação completa")
            self.logger.info(f"Total de tabelas para replicar estrutura: {len(all_tables)}")
            self.logger.info(f"Tabelas para replicar dados: {maintain_tables}")
            
            # Verificar conexões
            if not self.source_db.test_connection():
                self.logger.error("Erro na conexão com banco de origem")
                return False
            
            if not self.target_db.test_connection():
                self.logger.error("Erro na conexão com banco de destino")
                return False
            
            # Replicar estrutura de todas as tabelas
            if not self.replicate_structure(all_tables, maintain_tables, create_backup):
                return False
            
            # Replicar dados apenas das tabelas em maintain
            if maintain_tables:
                if not self.replicate_data(maintain_tables):
                    return False
            else:
                self.logger.info("Nenhuma tabela configurada para replicação de dados")
            
            self.logger.success("Replicação completa concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na replicação completa: {e}")
            return False
    
    def _create_table(self, table_name: str) -> bool:
        """Cria tabela no destino baseada na origem"""
        try:
            # Obter comando CREATE TABLE da origem
            create_statement = self.source_db.get_create_table_statement(table_name)
            
            if not create_statement:
                self.logger.error(f"Não foi possível obter CREATE TABLE para {table_name}")
                return False
            
            # Tentar criar tabela normalmente primeiro
            try:
                if self.target_db.execute_query(create_statement):
                    self.logger.success(f"Tabela {table_name} criada no destino")
                    return True
            except Exception as e:
                if "Foreign key constraint" in str(e):
                    self.logger.warning(f"Erro de chave estrangeira ao criar {table_name}, tentando sem constraints")
                    # Tentar criar sem constraints de chave estrangeira
                    return self._create_table_without_foreign_keys(table_name, create_statement)
                else:
                    raise e
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao criar tabela {table_name}: {e}")
            return False
    
    def _create_table_without_foreign_keys(self, table_name: str, original_statement: str) -> bool:
        """Cria tabela sem chaves estrangeiras, que serão adicionadas depois"""
        try:
            # Remover constraints de chave estrangeira do CREATE TABLE
            lines = original_statement.split('\n')
            filtered_lines = []
            
            for line in lines:
                line_stripped = line.strip()
                # Pular linhas que contêm FOREIGN KEY ou CONSTRAINT com FOREIGN KEY
                if ('FOREIGN KEY' in line_stripped or 
                    ('CONSTRAINT' in line_stripped and 'FOREIGN KEY' in line_stripped)):
                    continue
                # Remover vírgulas no final de linhas se a próxima linha foi removida
                filtered_lines.append(line)
            
            # Juntar as linhas e limpar vírgulas extras
            modified_statement = '\n'.join(filtered_lines)
            
            # Limpar vírgulas extras antes de parênteses de fechamento
            import re
            modified_statement = re.sub(r',\s*\)', ')', modified_statement)
            modified_statement = re.sub(r',\s*,', ',', modified_statement)
            
            # Executar no destino
            if self.target_db.execute_query(modified_statement):
                self.logger.success(f"Tabela {table_name} criada no destino (sem chaves estrangeiras)")
                return True
            else:
                self.logger.error(f"Erro ao criar tabela {table_name} sem chaves estrangeiras")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao criar tabela {table_name} sem chaves estrangeiras: {e}")
            return False
    
    def _alter_table(self, table_name: str, differences: List[Dict[str, Any]]) -> bool:
        """Altera estrutura da tabela"""
        try:
            alter_queries = []
            
            for diff in differences:
                if diff['type'] == 'missing_column':
                    # Adicionar coluna na posição correta
                    col_def = diff['source_definition']
                    query = f"ALTER TABLE {table_name} ADD COLUMN `{col_def['Field']}` {col_def['Type']}"
                    
                    if col_def['Null'] == 'NO':
                        query += " NOT NULL"
                    
                    if col_def['Default'] is not None:
                        # Tratar valores especiais do MySQL
                        default_val = col_def['Default']
                        if default_val.lower() in ['current_timestamp()', 'now()']:
                            query += f" DEFAULT {default_val}"
                        else:
                            query += f" DEFAULT '{default_val}'"
                    
                    # Adicionar extras como ON UPDATE
                    if col_def.get('Extra'):
                        query += f" {col_def['Extra']}"
                    
                    # Determinar posição da coluna
                    position = self._get_column_position(table_name, col_def['Field'])
                    if position:
                        query += f" {position}"
                    
                    alter_queries.append(query)
                
                elif diff['type'] == 'extra_column':
                    # Remover coluna
                    col_name = diff['column']
                    alter_queries.append(f"ALTER TABLE {table_name} DROP COLUMN `{col_name}`")
                
                elif diff['type'] == 'type_difference':
                    # Modificar tipo da coluna
                    col_name = diff['column']
                    source_type = diff['source_type']
                    alter_queries.append(f"ALTER TABLE {table_name} MODIFY COLUMN `{col_name}` {source_type}")
                
                elif diff['type'] == 'column_order_difference':
                    # Pular ordem de colunas por enquanto (muito complexo com FKs)
                    self.logger.warning(f"Ordem das colunas diferente em {table_name}, mas será ignorada para evitar problemas com chaves estrangeiras")
                    continue
            
            # Executar queries
            if alter_queries:
                self.logger.info(f"Executando {len(alter_queries)} alterações na tabela {table_name}")
                if not self.target_db.execute_queries(alter_queries):
                    self.logger.error(f"Erro ao alterar tabela {table_name}")
                    return False
            
            self.logger.success(f"Estrutura da tabela {table_name} alterada")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao alterar tabela {table_name}: {e}")
            return False
    
    def _recreate_table(self, table_name: str) -> bool:
        """Recria tabela para garantir estrutura idêntica"""
        try:
            # Criar tabela temporária
            temp_table = f"{table_name}_temp"
            
            # Remover tabela temporária se existir
            self.target_db.execute_query(f"DROP TABLE IF EXISTS {temp_table}")
            
            # Copiar dados para tabela temporária
            self.logger.info(f"Criando tabela temporária {temp_table}")
            create_temp = f"CREATE TABLE {temp_table} AS SELECT * FROM {table_name}"
            
            if not self.target_db.execute_query(create_temp):
                return False
            
            # Remover tabela original
            self.logger.info(f"Removendo tabela original {table_name}")
            if not self.target_db.execute_query(f"DROP TABLE {table_name}"):
                return False
            
            # Criar nova tabela com estrutura da origem
            if not self._create_table(table_name):
                return False
            
            # Copiar dados de volta
            self.logger.info(f"Copiando dados de volta para {table_name}")
            structure = self.target_db.get_table_structure(table_name)
            columns = [col['Field'] for col in structure]
            
            columns_str = ", ".join([f"`{col}`" for col in columns])
            copy_query = f"INSERT INTO {table_name} ({columns_str}) SELECT {columns_str} FROM {temp_table}"
            
            if not self.target_db.execute_query(copy_query):
                return False
            
            # Remover tabela temporária
            self.logger.info(f"Removendo tabela temporária {temp_table}")
            self.target_db.execute_query(f"DROP TABLE {temp_table}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao recriar tabela {table_name}: {e}")
            return False
    
    def _update_foreign_keys(self, table_name: str, differences: List[Dict[str, Any]]) -> bool:
        """Atualiza chaves estrangeiras"""
        try:
            queries = []
            
            for diff in differences:
                if diff['type'] == 'missing_foreign_key':
                    # Adicionar chave estrangeira
                    column = diff['column']
                    ref_table = diff['referenced_table']
                    ref_column = diff['referenced_column']
                    
                    constraint_name = f"fk_{table_name}_{column}"
                    query = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"
                    queries.append(query)
                
                elif diff['type'] == 'extra_foreign_key':
                    # Remover chave estrangeira
                    # Precisamos encontrar o nome da constraint
                    fks = self.target_db.get_table_foreign_keys(table_name)
                    for fk in fks:
                        if (fk['COLUMN_NAME'] == diff['column'] and 
                            fk['REFERENCED_TABLE_NAME'] == diff['referenced_table'] and
                            fk['REFERENCED_COLUMN_NAME'] == diff['referenced_column']):
                            
                            constraint_name = fk['CONSTRAINT_NAME']
                            query = f"ALTER TABLE {table_name} DROP FOREIGN KEY {constraint_name}"
                            queries.append(query)
                            break
            
            if queries:
                if not self.target_db.execute_queries(queries):
                    self.logger.error(f"Erro ao atualizar chaves estrangeiras da tabela {table_name}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar chaves estrangeiras da tabela {table_name}: {e}")
            return False
    
    def _update_indexes(self, table_name: str, differences: List[Dict[str, Any]]) -> bool:
        """Atualiza índices"""
        try:
            queries = []
            
            for diff in differences:
                if diff['type'] == 'missing_index':
                    # Adicionar índice
                    index_name = diff['index_name']
                    if index_name != 'PRIMARY':  # Não recriar chave primária
                        # Obter definição do índice da origem
                        source_indexes = self.source_db.get_table_indexes(table_name)
                        for idx in source_indexes:
                            if idx['Key_name'] == index_name:
                                # Criar comando CREATE INDEX
                                if idx['Non_unique'] == 0:
                                    query = f"CREATE UNIQUE INDEX {index_name} ON {table_name} ({idx['Column_name']})"
                                else:
                                    query = f"CREATE INDEX {index_name} ON {table_name} ({idx['Column_name']})"
                                queries.append(query)
                                break
                
                elif diff['type'] == 'extra_index':
                    # Remover índice
                    index_name = diff['index_name']
                    if index_name != 'PRIMARY':  # Não remover chave primária
                        query = f"DROP INDEX {index_name} ON {table_name}"
                        queries.append(query)
            
            if queries:
                if not self.target_db.execute_queries(queries):
                    self.logger.error(f"Erro ao atualizar índices da tabela {table_name}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar índices da tabela {table_name}: {e}")
            return False
    
    def _insert_data(self, table_name: str, columns: List[str], data: List[tuple]) -> bool:
        """Insere dados na tabela"""
        try:
            if not data:
                return True
            
            # Preparar query de inserção
            columns_str = ", ".join([f"`{col}`" for col in columns])
            placeholders = ", ".join(["%s"] * len(columns))
            query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
            
            # Inserir dados em lotes
            batch_size = 1000
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                
                try:
                    with self.target_db.get_connection() as conn:
                        cursor = conn.cursor()
                        cursor.executemany(query, batch)
                        conn.commit()
                except Exception as e:
                    self.logger.error(f"Erro ao inserir lote de dados na tabela {table_name}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao inserir dados na tabela {table_name}: {e}")
            return False
    
    def _add_missing_foreign_keys(self, tables: List[str]) -> bool:
        """Adiciona chaves estrangeiras que podem ter falhado na criação das tabelas"""
        try:
            for table_name in tables:
                # Obter chaves estrangeiras da origem
                source_fks = self.source_db.get_table_foreign_keys(table_name)
                target_fks = self.target_db.get_table_foreign_keys(table_name)
                
                # Converter para comparação
                source_fk_set = {
                    (fk['COLUMN_NAME'], fk['REFERENCED_TABLE_NAME'], fk['REFERENCED_COLUMN_NAME'])
                    for fk in source_fks
                }
                target_fk_set = {
                    (fk['COLUMN_NAME'], fk['REFERENCED_TABLE_NAME'], fk['REFERENCED_COLUMN_NAME'])
                    for fk in target_fks
                }
                
                # Chaves estrangeiras que faltam
                missing_fks = source_fk_set - target_fk_set
                
                if missing_fks:
                    self.logger.info(f"Adicionando {len(missing_fks)} chaves estrangeiras para {table_name}")
                    
                    for column, ref_table, ref_column in missing_fks:
                        # Verificar se a tabela referenciada existe
                        if self.target_db.table_exists(ref_table):
                            constraint_name = f"fk_{table_name}_{column}_{ref_table}"
                            query = f"ALTER TABLE {table_name} ADD CONSTRAINT {constraint_name} FOREIGN KEY ({column}) REFERENCES {ref_table}({ref_column})"
                            
                            try:
                                self.target_db.execute_query(query)
                                self.logger.info(f"Chave estrangeira adicionada: {table_name}.{column} -> {ref_table}.{ref_column}")
                            except Exception as e:
                                self.logger.warning(f"Erro ao adicionar chave estrangeira {table_name}.{column} -> {ref_table}.{ref_column}: {e}")
                        else:
                            self.logger.warning(f"Tabela referenciada {ref_table} não existe, pulando chave estrangeira")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar chaves estrangeiras: {e}")
            return False
    
    def _sort_tables_by_dependency(self, tables: List[str]) -> List[str]:
        """Ordena tabelas por dependência (tabelas sem dependências primeiro)"""
        try:
            # Mapear dependências de cada tabela
            dependencies = {}
            for table in tables:
                fks = self.source_db.get_table_foreign_keys(table)
                deps = [fk['REFERENCED_TABLE_NAME'] for fk in fks if fk['REFERENCED_TABLE_NAME'] in tables]
                dependencies[table] = deps
            
            # Ordenação topológica simples
            sorted_tables = []
            remaining = set(tables)
            
            while remaining:
                # Encontrar tabelas sem dependências pendentes
                no_deps = [table for table in remaining if not any(dep in remaining for dep in dependencies[table])]
                
                if not no_deps:
                    # Se não há tabelas sem dependências, adicionar uma para evitar loop infinito
                    no_deps = [list(remaining)[0]]
                
                for table in no_deps:
                    sorted_tables.append(table)
                    remaining.remove(table)
            
            return sorted_tables
            
        except Exception as e:
            self.logger.warning(f"Erro ao ordenar tabelas por dependência: {e}")
            return tables  # Retornar ordem original em caso de erro

    def _get_column_position(self, table_name: str, column_name: str) -> str:
        """Determina a posição correta da coluna baseada na estrutura da origem"""
        try:
            # Obter estrutura da origem
            source_structure = self.source_db.get_table_structure(table_name)
            source_columns = [col['Field'] for col in source_structure]
            
            # Obter estrutura do destino
            target_structure = self.target_db.get_table_structure(table_name)
            target_columns = [col['Field'] for col in target_structure]
            
            # Encontrar a posição da coluna na origem
            if column_name not in source_columns:
                return ""  # Coluna não encontrada na origem
            
            column_index = source_columns.index(column_name)
            
            # Se for a primeira coluna
            if column_index == 0:
                return "FIRST"
            
            # Encontrar a coluna anterior que existe no destino
            for i in range(column_index - 1, -1, -1):
                previous_column = source_columns[i]
                if previous_column in target_columns:
                    return f"AFTER `{previous_column}`"
            
            # Se não encontrou nenhuma coluna anterior, adicionar como primeira
            return "FIRST"
            
        except Exception as e:
            self.logger.warning(f"Erro ao determinar posição da coluna {column_name}: {e}")
            return ""  # Retornar vazio para adicionar no final
