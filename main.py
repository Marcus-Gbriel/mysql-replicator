#!/usr/bin/env python3
"""
Sistema de Replicação de Banco de Dados MySQL
Autor: Sistema Automatizado
Data: 2025

Este sistema permite replicar estrutura e dados entre bancos de dados MySQL,
mantendo sincronização entre ambientes de desenvolvimento e produção.
"""

import sys
import os
from cli_interface import CLIInterface

def main():
    """Função principal do sistema"""
    try:
        # Verificar se o arquivo de configuração existe
        if not os.path.exists('config.json'):
            print("Erro: Arquivo config.json não encontrado!")
            print("Certifique-se de que o arquivo de configuração existe no diretório atual.")
            sys.exit(1)
        
        # Inicializar interface CLI
        cli = CLIInterface()
        
        # Executar sistema
        cli.run()
        
    except KeyboardInterrupt:
        print("\n\nSistema interrompido pelo usuário.")
        sys.exit(0)
    except Exception as e:
        print(f"Erro fatal: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
