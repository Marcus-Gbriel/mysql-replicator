import mysql.connector
from mysql.connector import Error
from typing import Dict, List, Optional, Tuple, Any
from contextlib import contextmanager
from ..utils.logger import Logger

class DatabaseManager:
    def __init__(self, config: Dict[str, str], logger: Logger):
        self.config = config
        self.logger = logger
        self.connection = None
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexão com banco de dados"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['server'],
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password'],
                charset='utf8mb4',
                autocommit=False
            )
            yield self.connection
        except Error as e:
            self.logger.error(f"Erro ao conectar ao banco: {e}")
            raise
        finally:
            if self.connection and self.connection.is_connected():
                self.connection.close()
    
    def test_connection(self) -> bool:
        """Testa conexão com o banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                return True
        except Error as e:
            self.logger.error(f"Erro ao testar conexão: {e}")
            return False
    
    def get_all_tables(self) -> List[str]:
        """Retorna lista de todas as tabelas do banco"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SHOW TABLES")
                return [table[0] for table in cursor.fetchall()]
        except Error as e:
            self.logger.error(f"Erro ao obter tabelas: {e}")
            return []
    
    def get_table_structure(self, table_name: str) -> List[Dict[str, Any]]:
        """Retorna estrutura da tabela"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"DESCRIBE {table_name}")
                return cursor.fetchall()
        except Error as e:
            self.logger.error(f"Erro ao obter estrutura da tabela {table_name}: {e}")
            return []
    
    def get_table_foreign_keys(self, table_name: str) -> List[Dict[str, str]]:
        """Retorna chaves estrangeiras da tabela"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                query = """
                SELECT 
                    COLUMN_NAME,
                    REFERENCED_TABLE_NAME,
                    REFERENCED_COLUMN_NAME,
                    CONSTRAINT_NAME
                FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                WHERE TABLE_SCHEMA = %s 
                AND TABLE_NAME = %s 
                AND REFERENCED_TABLE_NAME IS NOT NULL
                """
                cursor.execute(query, (self.config['database'], table_name))
                return cursor.fetchall()
        except Error as e:
            self.logger.error(f"Erro ao obter chaves estrangeiras da tabela {table_name}: {e}")
            return []
    
    def get_table_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Retorna índices da tabela"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(f"SHOW INDEX FROM {table_name}")
                return cursor.fetchall()
        except Error as e:
            self.logger.error(f"Erro ao obter índices da tabela {table_name}: {e}")
            return []
    
    def get_create_table_statement(self, table_name: str) -> str:
        """Retorna comando CREATE TABLE da tabela"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SHOW CREATE TABLE {table_name}")
                return cursor.fetchone()[1]
        except Error as e:
            self.logger.error(f"Erro ao obter CREATE TABLE da tabela {table_name}: {e}")
            return ""
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> bool:
        """Executa uma query"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                conn.commit()
                return True
        except Error as e:
            self.logger.error(f"Erro ao executar query: {e}")
            return False
    
    def execute_queries(self, queries: List[str]) -> bool:
        """Executa múltiplas queries em uma transação"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                for query in queries:
                    cursor.execute(query)
                conn.commit()
                return True
        except Error as e:
            self.logger.error(f"Erro ao executar queries: {e}")
            return False
    
    def get_table_data(self, table_name: str) -> List[Tuple]:
        """Retorna todos os dados da tabela"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name}")
                return cursor.fetchall()
        except Error as e:
            self.logger.error(f"Erro ao obter dados da tabela {table_name}: {e}")
            return []
    
    def get_table_count(self, table_name: str) -> int:
        """Retorna número de registros da tabela"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                return cursor.fetchone()[0]
        except Error as e:
            self.logger.error(f"Erro ao contar registros da tabela {table_name}: {e}")
            return 0
    
    def table_exists(self, table_name: str) -> bool:
        """Verifica se a tabela existe"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = %s AND table_name = %s
                """, (self.config['database'], table_name))
                return cursor.fetchone()[0] > 0
        except Error as e:
            self.logger.error(f"Erro ao verificar existência da tabela {table_name}: {e}")
            return False
    
    def truncate_table(self, table_name: str) -> bool:
        """Limpa todos os dados da tabela, desabilitando verificações de chave estrangeira temporariamente"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Desabilitar verificações de chave estrangeira
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                
                # Truncar tabela
                cursor.execute(f"TRUNCATE TABLE {table_name}")
                
                # Reabilitar verificações de chave estrangeira
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                
                conn.commit()
                return True
        except Error as e:
            # Se TRUNCATE falhar, tentar DELETE
            try:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
                    cursor.execute(f"DELETE FROM {table_name}")
                    cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
                    conn.commit()
                    return True
            except Error as e2:
                self.logger.error(f"Erro ao limpar tabela {table_name}: {e2}")
                return False
    
    def copy_table_data(self, source_table: str, dest_table: str, columns: List[str]) -> bool:
        """Copia dados de uma tabela para outra"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                columns_str = ", ".join(columns)
                cursor.execute(f"INSERT INTO {dest_table} ({columns_str}) SELECT {columns_str} FROM {source_table}")
                conn.commit()
                return True
        except Error as e:
            self.logger.error(f"Erro ao copiar dados da tabela {source_table} para {dest_table}: {e}")
            return False
