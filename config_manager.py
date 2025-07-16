import json
import os
from typing import Dict, List, Any

class ConfigManager:
    def __init__(self, config_file="config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Carrega configurações do arquivo JSON"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Arquivo de configuração {self.config_file} não encontrado")
        except json.JSONDecodeError as e:
            raise ValueError(f"Erro ao decodificar JSON: {e}")
    
    def save_config(self):
        """Salva configurações no arquivo JSON"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=4, ensure_ascii=False)
    
    def get_database_config(self, environment: str) -> Dict[str, str]:
        """Retorna configurações do banco de dados para o ambiente especificado"""
        if environment not in self.config['database']:
            raise ValueError(f"Ambiente '{environment}' não encontrado na configuração")
        return self.config['database'][environment]
    
    def get_maintain_tables(self) -> List[str]:
        """Retorna lista de tabelas que devem ser mantidas"""
        return self.config['database'].get('maintain', [])
    
    def set_maintain_tables(self, tables: List[str]):
        """Define lista de tabelas que devem ser mantidas"""
        self.config['database']['maintain'] = tables
        self.save_config()
    
    def update_database_config(self, environment: str, config: Dict[str, str]):
        """Atualiza configurações do banco de dados para o ambiente especificado"""
        if environment not in self.config['database']:
            self.config['database'][environment] = {}
        self.config['database'][environment].update(config)
        self.save_config()
    
    def add_maintain_table(self, table: str):
        """Adiciona uma tabela à lista de maintain"""
        if table not in self.config['database']['maintain']:
            self.config['database']['maintain'].append(table)
            self.save_config()
    
    def remove_maintain_table(self, table: str):
        """Remove uma tabela da lista de maintain"""
        if table in self.config['database']['maintain']:
            self.config['database']['maintain'].remove(table)
            self.save_config()
    
    def get_all_environments(self) -> List[str]:
        """Retorna lista de todos os ambientes configurados"""
        return [env for env in self.config['database'].keys() if env != 'maintain']
