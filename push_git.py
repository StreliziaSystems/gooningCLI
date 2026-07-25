import subprocess
import sys
from pathlib import Path

REPO_URL = "https://github.com/StreliziaSystems/gooningCLI.git"


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def main():
    # Garante que você está dentro de um repositório git
    if not Path(".git").exists():
        print("Erro: este script precisa ser executado dentro da pasta do repositório Git.")
        sys.exit(1)

    commit_msg = input("Digite o nome da commit: ").strip()
    if not commit_msg:
        print("Erro: a mensagem da commit não pode ficar vazia.")
        sys.exit(1)

    try:
        print("\nAdicionando arquivos...")
        run(["git", "add", "-A"])

        print("Criando commit...")
        run(["git", "commit", "-m", commit_msg])

        print("Enviando para o GitHub...")
        run(["git", "push"])

        print("\nPronto! Alterações enviadas com sucesso.")
    except subprocess.CalledProcessError:
        print("\nDeu erro em alguma etapa.")
        print("Confirme se:")
        print("- você já configurou o remote do repositório")
        print("- está autenticado no GitHub")
        print("- há alterações para commitar")
        sys.exit(1)


if __name__ == "__main__":
    main()