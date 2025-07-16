from typing import Dict, List, Any, Tuple
from database_manager import DatabaseManager
from logger import Logger

class StructureAnalyzer:
    def __init__(self, source_db: DatabaseManager, target_db: DatabaseManager, logger: Logger):
        self.source_db = source_db
        self.target_db = target_db
        self.logger = logger
    
    def analyze_table_differences(self, table_name: str) -> Dict[str, Any]:
        """Analisa diferenças entre tabelas"""
        differences = {
            'table_name': table_name,
            'exists_in_source': False,
            'exists_in_target': False,
            'structure_differences': [],
            'foreign_key_differences': [],
            'index_differences': [],
            'data_count_source': 0,
            'data_count_target': 0
        }
        
        # Verificar existência das tabelas
        differences['exists_in_source'] = self.source_db.table_exists(table_name)
        differences['exists_in_target'] = self.target_db.table_exists(table_name)
        
        if not differences['exists_in_source']:
            self.logger.warning(f"Tabela {table_name} não existe na origem")
            return differences
        
        if not differences['exists_in_target']:
            self.logger.warning(f"Tabela {table_name} não existe no destino")
            return differences
        
        # Analisar estrutura
        source_structure = self.source_db.get_table_structure(table_name)
        target_structure = self.target_db.get_table_structure(table_name)
        
        differences['structure_differences'] = self._compare_structures(
            source_structure, target_structure
        )
        
        # Analisar chaves estrangeiras
        source_fks = self.source_db.get_table_foreign_keys(table_name)
        target_fks = self.target_db.get_table_foreign_keys(table_name)
        
        differences['foreign_key_differences'] = self._compare_foreign_keys(
            source_fks, target_fks
        )
        
        # Analisar índices
        source_indexes = self.source_db.get_table_indexes(table_name)
        target_indexes = self.target_db.get_table_indexes(table_name)
        
        differences['index_differences'] = self._compare_indexes(
            source_indexes, target_indexes
        )
        
        # Contar registros
        differences['data_count_source'] = self.source_db.get_table_count(table_name)
        differences['data_count_target'] = self.target_db.get_table_count(table_name)
        
        return differences
    
    def _compare_structures(self, source: List[Dict], target: List[Dict]) -> List[Dict[str, Any]]:
        """Compara estruturas de tabelas"""
        differences = []
        
        # Converter para dicionários para facilitar comparação
        source_cols = {col['Field']: col for col in source}
        target_cols = {col['Field']: col for col in target}
        
        # Verificar colunas que existem na origem mas não no destino
        for col_name in source_cols:
            if col_name not in target_cols:
                differences.append({
                    'type': 'missing_column',
                    'column': col_name,
                    'source_definition': source_cols[col_name],
                    'target_definition': None
                })
        
        # Verificar colunas que existem no destino mas não na origem
        for col_name in target_cols:
            if col_name not in source_cols:
                differences.append({
                    'type': 'extra_column',
                    'column': col_name,
                    'source_definition': None,
                    'target_definition': target_cols[col_name]
                })
        
        # Verificar diferenças em colunas comuns
        for col_name in source_cols:
            if col_name in target_cols:
                source_col = source_cols[col_name]
                target_col = target_cols[col_name]
                
                if source_col['Type'] != target_col['Type']:
                    differences.append({
                        'type': 'type_difference',
                        'column': col_name,
                        'source_type': source_col['Type'],
                        'target_type': target_col['Type']
                    })
                
                if source_col['Null'] != target_col['Null']:
                    differences.append({
                        'type': 'null_difference',
                        'column': col_name,
                        'source_null': source_col['Null'],
                        'target_null': target_col['Null']
                    })
                
                if source_col['Default'] != target_col['Default']:
                    differences.append({
                        'type': 'default_difference',
                        'column': col_name,
                        'source_default': source_col['Default'],
                        'target_default': target_col['Default']
                    })
        
        # Verificar ordem das colunas
        source_order = [col['Field'] for col in source]
        target_order = [col['Field'] for col in target]
        
        if source_order != target_order:
            differences.append({
                'type': 'column_order_difference',
                'source_order': source_order,
                'target_order': target_order
            })
        
        return differences
    
    def _compare_foreign_keys(self, source: List[Dict], target: List[Dict]) -> List[Dict[str, Any]]:
        """Compara chaves estrangeiras"""
        differences = []
        
        # Converter para sets para facilitar comparação
        source_fks = {
            (fk['COLUMN_NAME'], fk['REFERENCED_TABLE_NAME'], fk['REFERENCED_COLUMN_NAME'])
            for fk in source
        }
        target_fks = {
            (fk['COLUMN_NAME'], fk['REFERENCED_TABLE_NAME'], fk['REFERENCED_COLUMN_NAME'])
            for fk in target
        }
        
        # Chaves estrangeiras que existem na origem mas não no destino
        for fk in source_fks - target_fks:
            differences.append({
                'type': 'missing_foreign_key',
                'column': fk[0],
                'referenced_table': fk[1],
                'referenced_column': fk[2]
            })
        
        # Chaves estrangeiras que existem no destino mas não na origem
        for fk in target_fks - source_fks:
            differences.append({
                'type': 'extra_foreign_key',
                'column': fk[0],
                'referenced_table': fk[1],
                'referenced_column': fk[2]
            })
        
        return differences
    
    def _compare_indexes(self, source: List[Dict], target: List[Dict]) -> List[Dict[str, Any]]:
        """Compara índices"""
        differences = []
        
        # Agrupar índices por nome
        source_indexes = {}
        for idx in source:
            if idx['Key_name'] not in source_indexes:
                source_indexes[idx['Key_name']] = []
            source_indexes[idx['Key_name']].append(idx)
        
        target_indexes = {}
        for idx in target:
            if idx['Key_name'] not in target_indexes:
                target_indexes[idx['Key_name']] = []
            target_indexes[idx['Key_name']].append(idx)
        
        # Comparar índices
        for index_name in source_indexes:
            if index_name not in target_indexes:
                differences.append({
                    'type': 'missing_index',
                    'index_name': index_name,
                    'index_definition': source_indexes[index_name]
                })
        
        for index_name in target_indexes:
            if index_name not in source_indexes:
                differences.append({
                    'type': 'extra_index',
                    'index_name': index_name,
                    'index_definition': target_indexes[index_name]
                })
        
        return differences
    
    def analyze_all_tables(self, table_names: List[str], maintain_tables: List[str] = None) -> Dict[str, Any]:
        """Analisa todas as tabelas especificadas"""
        if maintain_tables is None:
            maintain_tables = []
            
        analysis = {
            'total_tables': len(table_names),
            'tables_analyzed': 0,
            'tables_with_differences': 0,
            'table_analyses': {}
        }
        
        for table_name in table_names:
            self.logger.info(f"Analisando tabela: {table_name}")
            
            table_analysis = self.analyze_table_differences(table_name)
            analysis['table_analyses'][table_name] = table_analysis
            analysis['tables_analyzed'] += 1
            
            # Verificar se há diferenças
            has_differences = (
                not table_analysis['exists_in_target'] or
                table_analysis['structure_differences'] or
                table_analysis['foreign_key_differences'] or
                table_analysis['index_differences']
            )
            
            # Para tabelas em maintain, também verificar diferenças de dados
            if table_name in maintain_tables:
                has_differences = has_differences or (table_analysis['data_count_source'] != table_analysis['data_count_target'])
            
            if has_differences:
                analysis['tables_with_differences'] += 1
        
        return analysis
    
    def get_replication_plan(self, table_names: List[str], maintain_tables: List[str] = None) -> List[Dict[str, Any]]:
        """Gera plano de replicação"""
        if maintain_tables is None:
            maintain_tables = []
            
        plan = []
        
        for table_name in table_names:
            table_analysis = self.analyze_table_differences(table_name)
            
            if not table_analysis['exists_in_source']:
                continue
            
            step = {
                'table': table_name,
                'actions': [],
                'is_maintain_table': table_name in maintain_tables
            }
            
            # Se a tabela não existe no destino, precisa ser criada
            if not table_analysis['exists_in_target']:
                step['actions'].append({
                    'type': 'create_table',
                    'description': f'Criar tabela {table_name}'
                })
            else:
                # Verificar se há diferenças estruturais
                if table_analysis['structure_differences']:
                    step['actions'].append({
                        'type': 'alter_table',
                        'description': f'Alterar estrutura da tabela {table_name}',
                        'differences': table_analysis['structure_differences']
                    })
                
                # Verificar chaves estrangeiras
                if table_analysis['foreign_key_differences']:
                    step['actions'].append({
                        'type': 'update_foreign_keys',
                        'description': f'Atualizar chaves estrangeiras da tabela {table_name}',
                        'differences': table_analysis['foreign_key_differences']
                    })
                
                # Verificar índices
                if table_analysis['index_differences']:
                    step['actions'].append({
                        'type': 'update_indexes',
                        'description': f'Atualizar índices da tabela {table_name}',
                        'differences': table_analysis['index_differences']
                    })
            
            # Replicar dados apenas para tabelas em maintain
            if table_name in maintain_tables:
                step['actions'].append({
                    'type': 'replicate_data',
                    'description': f'Replicar dados da tabela {table_name}',
                    'source_count': table_analysis['data_count_source'],
                    'target_count': table_analysis['data_count_target']
                })
            
            if step['actions']:
                plan.append(step)
        
        return plan
