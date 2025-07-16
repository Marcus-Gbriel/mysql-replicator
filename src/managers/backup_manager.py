import os
import shutil
from datetime import datetime
from typing import List, Dict, Any
from .database_manager import DatabaseManager
from ..utils.logger import Logger

class BackupManager:
    def __init__(self, logger: Logger):
        self.logger = logger
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def create_backup(self, db_manager: DatabaseManager, environment: str, tables: List[str] = None) -> str:
        """Cria backup do banco de dados"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{environment}_{timestamp}"
        backup_path = os.path.join(self.backup_dir, backup_name)
        
        os.makedirs(backup_path, exist_ok=True)
        
        try:
            # Se não especificar tabelas, fazer backup de todas
            if tables is None:
                tables = db_manager.get_all_tables()
            
            self.logger.info(f"Iniciando backup de {len(tables)} tabelas para {environment}")
            
            # Criar arquivo de metadados
            metadata = {
                'timestamp': timestamp,
                'environment': environment,
                'tables': tables,
                'database': db_manager.config['database']
            }
            
            metadata_file = os.path.join(backup_path, 'metadata.json')
            with open(metadata_file, 'w', encoding='utf-8') as f:
                import json
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Fazer backup de cada tabela
            for table in tables:
                if db_manager.table_exists(table):
                    self._backup_table(db_manager, table, backup_path)
                else:
                    self.logger.warning(f"Tabela {table} não existe, pulando backup")
            
            self.logger.success(f"Backup criado com sucesso: {backup_name}")
            return backup_name
            
        except Exception as e:
            self.logger.error(f"Erro ao criar backup: {e}")
            # Limpar backup incompleto
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
            raise
    
    def _backup_table(self, db_manager: DatabaseManager, table_name: str, backup_path: str):
        """Faz backup de uma tabela específica"""
        try:
            # Backup da estrutura
            create_statement = db_manager.get_create_table_statement(table_name)
            structure_file = os.path.join(backup_path, f"{table_name}_structure.sql")
            
            with open(structure_file, 'w', encoding='utf-8') as f:
                f.write(f"-- Estrutura da tabela {table_name}\n")
                f.write(f"-- Backup criado em: {datetime.now()}\n\n")
                f.write(f"DROP TABLE IF EXISTS {table_name};\n")
                f.write(create_statement + ";\n")
            
            # Backup dos dados
            data_file = os.path.join(backup_path, f"{table_name}_data.sql")
            self._backup_table_data(db_manager, table_name, data_file)
            
            self.logger.info(f"Backup da tabela {table_name} concluído")
            
        except Exception as e:
            self.logger.error(f"Erro ao fazer backup da tabela {table_name}: {e}")
            raise
    
    def _backup_table_data(self, db_manager: DatabaseManager, table_name: str, data_file: str):
        """Faz backup dos dados de uma tabela"""
        try:
            with open(data_file, 'w', encoding='utf-8') as f:
                f.write(f"-- Dados da tabela {table_name}\n")
                f.write(f"-- Backup criado em: {datetime.now()}\n\n")
                
                # Obter estrutura da tabela para gerar INSERT statements
                structure = db_manager.get_table_structure(table_name)
                columns = [col['Field'] for col in structure]
                
                if not columns:
                    f.write(f"-- Tabela {table_name} não possui colunas\n")
                    return
                
                # Obter dados
                data = db_manager.get_table_data(table_name)
                
                if not data:
                    f.write(f"-- Tabela {table_name} não possui dados\n")
                    return
                
                # Desabilitar verificações de chave estrangeira
                f.write("SET FOREIGN_KEY_CHECKS = 0;\n")
                f.write(f"TRUNCATE TABLE {table_name};\n\n")
                
                # Gerar INSERT statements
                columns_str = ", ".join([f"`{col}`" for col in columns])
                
                for row in data:
                    values = []
                    for value in row:
                        if value is None:
                            values.append("NULL")
                        elif isinstance(value, str):
                            # Escapar aspas simples
                            escaped_value = value.replace("'", "''")
                            values.append(f"'{escaped_value}'")
                        elif isinstance(value, (int, float)):
                            values.append(str(value))
                        else:
                            values.append(f"'{str(value)}'")
                    
                    values_str = ", ".join(values)
                    f.write(f"INSERT INTO {table_name} ({columns_str}) VALUES ({values_str});\n")
                
                # Reabilitar verificações de chave estrangeira
                f.write("\nSET FOREIGN_KEY_CHECKS = 1;\n")
                
        except Exception as e:
            self.logger.error(f"Erro ao fazer backup dos dados da tabela {table_name}: {e}")
            raise
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """Lista todos os backups disponíveis"""
        backups = []
        
        try:
            for backup_name in os.listdir(self.backup_dir):
                backup_path = os.path.join(self.backup_dir, backup_name)
                
                if os.path.isdir(backup_path):
                    metadata_file = os.path.join(backup_path, 'metadata.json')
                    
                    if os.path.exists(metadata_file):
                        try:
                            with open(metadata_file, 'r', encoding='utf-8') as f:
                                import json
                                metadata = json.load(f)
                                
                                # Calcular tamanho do backup
                                backup_size = self._calculate_backup_size(backup_path)
                                
                                backups.append({
                                    'name': backup_name,
                                    'path': backup_path,
                                    'timestamp': metadata['timestamp'],
                                    'environment': metadata['environment'],
                                    'database': metadata['database'],
                                    'tables': metadata['tables'],
                                    'table_count': len(metadata['tables']),
                                    'size': backup_size
                                })
                        except Exception as e:
                            self.logger.warning(f"Erro ao ler metadata do backup {backup_name}: {e}")
            
            # Ordenar por timestamp (mais recente primeiro)
            backups.sort(key=lambda x: x['timestamp'], reverse=True)
            
        except Exception as e:
            self.logger.error(f"Erro ao listar backups: {e}")
        
        return backups
    
    def _calculate_backup_size(self, backup_path: str) -> int:
        """Calcula tamanho total do backup em bytes"""
        total_size = 0
        try:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
        except Exception as e:
            self.logger.warning(f"Erro ao calcular tamanho do backup: {e}")
        
        return total_size
    
    def format_size(self, size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def delete_backup(self, backup_name: str) -> bool:
        """Remove um backup específico"""
        try:
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            if os.path.exists(backup_path):
                shutil.rmtree(backup_path)
                self.logger.success(f"Backup {backup_name} removido com sucesso")
                return True
            else:
                self.logger.warning(f"Backup {backup_name} não encontrado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao remover backup {backup_name}: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Remove backups antigos, mantendo apenas os mais recentes"""
        try:
            backups = self.list_backups()
            
            if len(backups) <= keep_count:
                return 0
            
            # Remover backups antigos
            backups_to_remove = backups[keep_count:]
            removed_count = 0
            
            for backup in backups_to_remove:
                if self.delete_backup(backup['name']):
                    removed_count += 1
            
            self.logger.info(f"Removidos {removed_count} backups antigos")
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Erro ao limpar backups antigos: {e}")
            return 0
