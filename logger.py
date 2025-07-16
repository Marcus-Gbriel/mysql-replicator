import logging
import os
from datetime import datetime
from colorama import Fore, Style, init

# Inicializa colorama para Windows
init()

class Logger:
    def __init__(self, log_dir="logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Configurar logging
        log_file = os.path.join(log_dir, f"replicator_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def info(self, message):
        """Log informações"""
        self.logger.info(message)
        print(f"{Fore.BLUE}[INFO]{Style.RESET_ALL} {message}")
    
    def success(self, message):
        """Log sucesso"""
        self.logger.info(f"SUCCESS: {message}")
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {message}")
    
    def warning(self, message):
        """Log avisos"""
        self.logger.warning(message)
        print(f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL} {message}")
    
    def error(self, message):
        """Log erros"""
        self.logger.error(message)
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {message}")
    
    def critical(self, message):
        """Log erros críticos"""
        self.logger.critical(message)
        print(f"{Fore.RED}[CRITICAL]{Style.RESET_ALL} {message}")
