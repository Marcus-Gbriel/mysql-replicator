import os
import json
from typing import List, Dict, Any
from colorama import Fore, Style
from tabulate import tabulate
from config_manager import ConfigManager
from database_manager import DatabaseManager
from structure_analyzer import StructureAnalyzer
from backup_manager import BackupManager
from replicator import Replicator
from logger import Logger

class CLIInterface:
    def __init__(self):
        self.logger = Logger()
        self.config_manager = ConfigManager()
        self.backup_manager = BackupManager(self.logger)
        
        # Inicializar gerenciadores de banco
        self.source_db = None
        self.target_db = None
        self.replicator = None
        
        self._initialize_databases()
    
    def _initialize_databases(self):
        """Inicializa conexões com bancos de dados"""
        try:
            # Configurações dos bancos
            source_config = self.config_manager.get_database_config('development')
            target_config = self.config_manager.get_database_config('production')
            
            # Inicializar gerenciadores
            self.source_db = DatabaseManager(source_config, self.logger)
            self.target_db = DatabaseManager(target_config, self.logger)
            
            # Inicializar replicador
            self.replicator = Replicator(
                self.source_db, 
                self.target_db, 
                self.backup_manager, 
                self.logger
            )
            
        except Exception as e:
            self.logger.error(f"Erro ao inicializar bancos de dados: {e}")
            self.source_db = None
            self.target_db = None
            self.replicator = None
    
    def run(self):
        """Executa interface CLI"""
        self.logger.info("Iniciando Sistema de Replicação de Banco de Dados")
        
        while True:
            self._show_main_menu()
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '1':
                self._analyze_replication_menu()
            elif choice == '2':
                self._backups_menu()
            elif choice == '3':
                self._replication_menu()
            elif choice == '4':
                self._configuration_menu()
            elif choice == '5':
                self._test_connections()
            elif choice == '0':
                self.logger.info("Saindo do sistema...")
                break
            else:
                print(f"{Fore.RED}Opção inválida! Tente novamente.{Style.RESET_ALL}")
    
    def _show_main_menu(self):
        """Mostra menu principal"""
        print(f"\n{Fore.CYAN}{'='*50}")
        print("    SISTEMA DE REPLICAÇÃO DE BANCO DE DADOS")
        print(f"{'='*50}{Style.RESET_ALL}")
        print(f"{Fore.WHITE}1. Analisar Replicação{Style.RESET_ALL}")
        print(f"{Fore.WHITE}2. Backups{Style.RESET_ALL}")
        print(f"{Fore.WHITE}3. Replicação{Style.RESET_ALL}")
        print(f"{Fore.WHITE}4. Configuração{Style.RESET_ALL}")
        print(f"{Fore.WHITE}5. Testar Conexões{Style.RESET_ALL}")
        print(f"{Fore.RED}0. Sair{Style.RESET_ALL}")
    
    def _analyze_replication_menu(self):
        """Menu de análise de replicação"""
        if not self._check_database_connections():
            return
        
        # Obter todas as tabelas do banco de desenvolvimento
        all_tables = self.source_db.get_all_tables()
        maintain_tables = self.config_manager.get_maintain_tables()
        
        if not all_tables:
            print(f"{Fore.RED}Nenhuma tabela encontrada no banco de desenvolvimento!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Analisando replicação...{Style.RESET_ALL}")
        print(f"Total de tabelas no desenvolvimento: {len(all_tables)}")
        print(f"Tabelas para replicar estrutura: {len(all_tables)} (todas)")
        print(f"Tabelas para replicar dados: {len(maintain_tables)} ({', '.join(maintain_tables) if maintain_tables else 'nenhuma'})")
        
        analyzer = StructureAnalyzer(self.source_db, self.target_db, self.logger)
        analysis = analyzer.analyze_all_tables(all_tables, maintain_tables)
        
        self._display_analysis_results(analysis, maintain_tables)
        
        # Perguntar se deseja fazer replicação
        if analysis['tables_with_differences'] > 0:
            choice = input(f"\n{Fore.YELLOW}Deseja fazer a replicação? (s/n): {Style.RESET_ALL}").strip().lower()
            if choice in ['s', 'sim', 'y', 'yes']:
                self._perform_full_replication(all_tables, maintain_tables)
    
    def _display_analysis_results(self, analysis: Dict[str, Any], maintain_tables: List[str] = None):
        """Exibe resultados da análise"""
        if maintain_tables is None:
            maintain_tables = []
            
        print(f"\n{Fore.GREEN}Resumo da Análise:{Style.RESET_ALL}")
        print(f"Total de tabelas analisadas: {analysis['tables_analyzed']}")
        print(f"Tabelas com diferenças: {analysis['tables_with_differences']}")
        
        if analysis['tables_with_differences'] == 0:
            print(f"{Fore.GREEN}Todas as tabelas estão sincronizadas!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.YELLOW}Detalhes das Diferenças:{Style.RESET_ALL}")
        
        for table_name, table_analysis in analysis['table_analyses'].items():
            is_maintain_table = table_name in maintain_tables
            table_prefix = f"[MAINTAIN] " if is_maintain_table else "[STRUCTURE] "
            
            if not table_analysis['exists_in_source']:
                print(f"{Fore.RED}❌ {table_prefix}{table_name}: Não existe na origem{Style.RESET_ALL}")
                continue
            
            if not table_analysis['exists_in_target']:
                print(f"{Fore.RED}❌ {table_prefix}{table_name}: Não existe no destino{Style.RESET_ALL}")
                continue
            
            differences = []
            if table_analysis['structure_differences']:
                differences.append(f"{len(table_analysis['structure_differences'])} diferenças estruturais")
            
            if table_analysis['foreign_key_differences']:
                differences.append(f"{len(table_analysis['foreign_key_differences'])} diferenças de chaves estrangeiras")
            
            if table_analysis['index_differences']:
                differences.append(f"{len(table_analysis['index_differences'])} diferenças de índices")
            
            # Só mostrar diferenças de dados para tabelas em maintain
            if is_maintain_table and table_analysis['data_count_source'] != table_analysis['data_count_target']:
                differences.append(f"Dados: {table_analysis['data_count_source']} → {table_analysis['data_count_target']}")
            
            if differences:
                print(f"{Fore.YELLOW}⚠️  {table_prefix}{table_name}: {', '.join(differences)}{Style.RESET_ALL}")
            else:
                print(f"{Fore.GREEN}✅ {table_prefix}{table_name}: Sincronizado{Style.RESET_ALL}")
        
        print(f"\n{Fore.CYAN}Legenda:{Style.RESET_ALL}")
        print(f"[MAINTAIN] = Estrutura + Dados serão replicados")
        print(f"[STRUCTURE] = Apenas estrutura será replicada")
    
    def _backups_menu(self):
        """Menu de backups"""
        while True:
            print(f"\n{Fore.CYAN}Menu de Backups{Style.RESET_ALL}")
            print("1. Listar Backups")
            print("2. Criar Backup de Produção")
            print("3. Criar Backup de Desenvolvimento")
            print("4. Remover Backup")
            print("5. Limpar Backups Antigos")
            print("0. Voltar")
            
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '1':
                self._list_backups()
            elif choice == '2':
                self._create_backup('production')
            elif choice == '3':
                self._create_backup('development')
            elif choice == '4':
                self._remove_backup()
            elif choice == '5':
                self._cleanup_backups()
            elif choice == '0':
                break
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
    
    def _list_backups(self):
        """Lista todos os backups"""
        backups = self.backup_manager.list_backups()
        
        if not backups:
            print(f"{Fore.YELLOW}Nenhum backup encontrado.{Style.RESET_ALL}")
            return
        
        # Preparar dados para tabela
        table_data = []
        for backup in backups:
            table_data.append([
                backup['name'],
                backup['environment'],
                backup['database'],
                backup['table_count'],
                self.backup_manager.format_size(backup['size']),
                backup['timestamp']
            ])
        
        headers = ['Nome', 'Ambiente', 'Banco', 'Tabelas', 'Tamanho', 'Data/Hora']
        print(f"\n{Fore.GREEN}Backups Disponíveis:{Style.RESET_ALL}")
        print(tabulate(table_data, headers=headers, tablefmt='grid'))
    
    def _create_backup(self, environment: str):
        """Cria backup"""
        if not self._check_database_connections():
            return
        
        # Obter todas as tabelas do ambiente
        db_manager = self.target_db if environment == 'production' else self.source_db
        all_tables = db_manager.get_all_tables()
        
        if not all_tables:
            print(f"{Fore.RED}Nenhuma tabela encontrada no banco de {environment}!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Criando backup de {environment}...{Style.RESET_ALL}")
        print(f"Total de tabelas: {len(all_tables)}")
        
        try:
            backup_name = self.backup_manager.create_backup(db_manager, environment, all_tables)
            print(f"{Fore.GREEN}Backup criado com sucesso: {backup_name}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Erro ao criar backup: {e}{Style.RESET_ALL}")
    
    def _remove_backup(self):
        """Remove backup"""
        backups = self.backup_manager.list_backups()
        
        if not backups:
            print(f"{Fore.YELLOW}Nenhum backup encontrado.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Backups Disponíveis:{Style.RESET_ALL}")
        for i, backup in enumerate(backups, 1):
            print(f"{i}. {backup['name']} ({backup['environment']} - {backup['timestamp']})")
        
        try:
            choice = int(input("\nEscolha o backup para remover (0 para cancelar): ").strip())
            
            if choice == 0:
                return
            
            if 1 <= choice <= len(backups):
                backup_name = backups[choice - 1]['name']
                confirm = input(f"Confirma remoção do backup {backup_name}? (s/n): ").strip().lower()
                
                if confirm in ['s', 'sim', 'y', 'yes']:
                    if self.backup_manager.delete_backup(backup_name):
                        print(f"{Fore.GREEN}Backup removido com sucesso!{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.RED}Erro ao remover backup!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
                
        except ValueError:
            print(f"{Fore.RED}Entrada inválida!{Style.RESET_ALL}")
    
    def _cleanup_backups(self):
        """Limpa backups antigos"""
        try:
            keep_count = int(input("Quantos backups manter? (padrão: 10): ").strip() or "10")
            
            removed = self.backup_manager.cleanup_old_backups(keep_count)
            
            if removed > 0:
                print(f"{Fore.GREEN}Removidos {removed} backups antigos.{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}Nenhum backup antigo para remover.{Style.RESET_ALL}")
                
        except ValueError:
            print(f"{Fore.RED}Entrada inválida!{Style.RESET_ALL}")
    
    def _replication_menu(self):
        """Menu de replicação"""
        if not self._check_database_connections():
            return
        
        # Obter todas as tabelas do banco de desenvolvimento
        all_tables = self.source_db.get_all_tables()
        maintain_tables = self.config_manager.get_maintain_tables()
        
        if not all_tables:
            print(f"{Fore.RED}Nenhuma tabela encontrada no banco de desenvolvimento!{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Replicação Completa{Style.RESET_ALL}")
        print(f"Total de tabelas para replicar estrutura: {len(all_tables)}")
        print(f"Tabelas para replicar dados: {len(maintain_tables)} ({', '.join(maintain_tables) if maintain_tables else 'nenhuma'})")
        
        print(f"\n{Fore.YELLOW}Estrutura será replicada para:{Style.RESET_ALL}")
        for table in sorted(all_tables):
            print(f"  • {table}")
        
        if maintain_tables:
            print(f"\n{Fore.YELLOW}Dados serão replicados para:{Style.RESET_ALL}")
            for table in sorted(maintain_tables):
                print(f"  • {table}")
        
        confirm = input(f"\n{Fore.YELLOW}Confirma replicação completa? (s/n): {Style.RESET_ALL}").strip().lower()
        
        if confirm in ['s', 'sim', 'y', 'yes']:
            self._perform_full_replication(all_tables, maintain_tables)
    
    def _perform_full_replication(self, all_tables: List[str], maintain_tables: List[str]):
        """Executa replicação completa"""
        print(f"\n{Fore.CYAN}Iniciando replicação completa...{Style.RESET_ALL}")
        
        # Perguntar sobre backup
        backup_choice = input("Criar backup antes da replicação? (s/n): ").strip().lower()
        create_backup = backup_choice in ['s', 'sim', 'y', 'yes']
        
        success = self.replicator.full_replication(all_tables, maintain_tables, create_backup)
        
        if success:
            print(f"\n{Fore.GREEN}Replicação concluída com sucesso!{Style.RESET_ALL}")
            print(f"Estrutura replicada para {len(all_tables)} tabelas")
            print(f"Dados replicados para {len(maintain_tables)} tabelas")
        else:
            print(f"\n{Fore.RED}Erro na replicação!{Style.RESET_ALL}")
    
    def _configuration_menu(self):
        """Menu de configuração"""
        while True:
            print(f"\n{Fore.CYAN}Menu de Configuração{Style.RESET_ALL}")
            print("1. Configurar Banco de Dados")
            print("2. Gerenciar Tabelas de Manutenção")
            print("3. Visualizar Configuração Atual")
            print("0. Voltar")
            
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '1':
                self._configure_database()
            elif choice == '2':
                self._manage_maintain_tables()
            elif choice == '3':
                self._show_current_config()
            elif choice == '0':
                break
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
    
    def _configure_database(self):
        """Configura banco de dados"""
        print(f"\n{Fore.CYAN}Configuração de Banco de Dados{Style.RESET_ALL}")
        
        environments = self.config_manager.get_all_environments()
        
        print("Ambientes disponíveis:")
        for i, env in enumerate(environments, 1):
            print(f"{i}. {env}")
        
        try:
            choice = int(input("\nEscolha o ambiente para configurar: ").strip())
            
            if 1 <= choice <= len(environments):
                environment = environments[choice - 1]
                current_config = self.config_manager.get_database_config(environment)
                
                print(f"\n{Fore.YELLOW}Configuração atual de {environment}:{Style.RESET_ALL}")
                print(f"Servidor: {current_config['server']}")
                print(f"Banco: {current_config['database']}")
                print(f"Usuário: {current_config['user']}")
                print(f"Senha: {'*' * len(current_config['password'])}")
                
                print(f"\n{Fore.CYAN}Nova configuração (deixe em branco para manter atual):{Style.RESET_ALL}")
                
                server = input(f"Servidor [{current_config['server']}]: ").strip()
                database = input(f"Banco [{current_config['database']}]: ").strip()
                user = input(f"Usuário [{current_config['user']}]: ").strip()
                password = input(f"Senha [atual]: ").strip()
                
                new_config = {}
                if server:
                    new_config['server'] = server
                if database:
                    new_config['database'] = database
                if user:
                    new_config['user'] = user
                if password:
                    new_config['password'] = password
                
                if new_config:
                    self.config_manager.update_database_config(environment, new_config)
                    print(f"{Fore.GREEN}Configuração atualizada com sucesso!{Style.RESET_ALL}")
                    
                    # Reinicializar conexões
                    self._initialize_databases()
                else:
                    print(f"{Fore.YELLOW}Nenhuma alteração feita.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
                
        except ValueError:
            print(f"{Fore.RED}Entrada inválida!{Style.RESET_ALL}")
    
    def _manage_maintain_tables(self):
        """Gerencia tabelas de manutenção"""
        while True:
            maintain_tables = self.config_manager.get_maintain_tables()
            
            print(f"\n{Fore.CYAN}Tabelas de Manutenção{Style.RESET_ALL}")
            print(f"Tabelas atuais: {', '.join(maintain_tables) if maintain_tables else 'Nenhuma'}")
            
            print("\n1. Adicionar Tabela")
            print("2. Remover Tabela")
            print("3. Listar Todas as Tabelas do Banco")
            print("0. Voltar")
            
            choice = input("\nEscolha uma opção: ").strip()
            
            if choice == '1':
                self._add_maintain_table()
            elif choice == '2':
                self._remove_maintain_table()
            elif choice == '3':
                self._list_all_tables()
            elif choice == '0':
                break
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
    
    def _add_maintain_table(self):
        """Adiciona tabela à lista de manutenção"""
        table_name = input("Nome da tabela para adicionar: ").strip()
        
        if table_name:
            self.config_manager.add_maintain_table(table_name)
            print(f"{Fore.GREEN}Tabela '{table_name}' adicionada à lista de manutenção.{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Nome da tabela não pode estar vazio!{Style.RESET_ALL}")
    
    def _remove_maintain_table(self):
        """Remove tabela da lista de manutenção"""
        maintain_tables = self.config_manager.get_maintain_tables()
        
        if not maintain_tables:
            print(f"{Fore.YELLOW}Nenhuma tabela na lista de manutenção.{Style.RESET_ALL}")
            return
        
        print(f"\n{Fore.CYAN}Tabelas na lista de manutenção:{Style.RESET_ALL}")
        for i, table in enumerate(maintain_tables, 1):
            print(f"{i}. {table}")
        
        try:
            choice = int(input("\nEscolha a tabela para remover (0 para cancelar): ").strip())
            
            if choice == 0:
                return
            
            if 1 <= choice <= len(maintain_tables):
                table_name = maintain_tables[choice - 1]
                self.config_manager.remove_maintain_table(table_name)
                print(f"{Fore.GREEN}Tabela '{table_name}' removida da lista de manutenção.{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Opção inválida!{Style.RESET_ALL}")
                
        except ValueError:
            print(f"{Fore.RED}Entrada inválida!{Style.RESET_ALL}")
    
    def _list_all_tables(self):
        """Lista todas as tabelas do banco"""
        if not self._check_database_connections():
            return
        
        print(f"\n{Fore.CYAN}Tabelas no banco de desenvolvimento:{Style.RESET_ALL}")
        dev_tables = self.source_db.get_all_tables()
        
        if dev_tables:
            for table in sorted(dev_tables):
                print(f"  • {table}")
        else:
            print(f"{Fore.YELLOW}Nenhuma tabela encontrada.{Style.RESET_ALL}")
    
    def _show_current_config(self):
        """Mostra configuração atual"""
        print(f"\n{Fore.CYAN}Configuração Atual{Style.RESET_ALL}")
        
        environments = self.config_manager.get_all_environments()
        
        for env in environments:
            config = self.config_manager.get_database_config(env)
            print(f"\n{Fore.YELLOW}{env.upper()}:{Style.RESET_ALL}")
            print(f"  Servidor: {config['server']}")
            print(f"  Banco: {config['database']}")
            print(f"  Usuário: {config['user']}")
            print(f"  Senha: {'*' * len(config['password'])}")
        
        maintain_tables = self.config_manager.get_maintain_tables()
        print(f"\n{Fore.YELLOW}Tabelas de Manutenção:{Style.RESET_ALL}")
        if maintain_tables:
            for table in maintain_tables:
                print(f"  • {table}")
        else:
            print(f"  {Fore.YELLOW}Nenhuma tabela configurada{Style.RESET_ALL}")
    
    def _test_connections(self):
        """Testa conexões com os bancos"""
        print(f"\n{Fore.CYAN}Testando conexões...{Style.RESET_ALL}")
        
        if self.source_db:
            if self.source_db.test_connection():
                print(f"{Fore.GREEN}✅ Conexão com banco de desenvolvimento: OK{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Conexão com banco de desenvolvimento: FALHA{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Gerenciador de banco de desenvolvimento não inicializado{Style.RESET_ALL}")
        
        if self.target_db:
            if self.target_db.test_connection():
                print(f"{Fore.GREEN}✅ Conexão com banco de produção: OK{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}❌ Conexão com banco de produção: FALHA{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}❌ Gerenciador de banco de produção não inicializado{Style.RESET_ALL}")
    
    def _check_database_connections(self) -> bool:
        """Verifica se as conexões estão ativas"""
        if not self.source_db or not self.target_db:
            print(f"{Fore.RED}Erro: Conexões com banco de dados não inicializadas!{Style.RESET_ALL}")
            return False
        
        if not self.source_db.test_connection():
            print(f"{Fore.RED}Erro: Não foi possível conectar ao banco de desenvolvimento!{Style.RESET_ALL}")
            return False
        
        if not self.target_db.test_connection():
            print(f"{Fore.RED}Erro: Não foi possível conectar ao banco de produção!{Style.RESET_ALL}")
            return False
        
        return True
