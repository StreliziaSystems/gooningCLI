import subprocess
import sys
from pathlib import Path


def run(cmd, check=True):
    return subprocess.run(cmd, check=check)


def get_current_branch():
    result = subprocess.run(
        ["git", "branch", "--show-current"],
        capture_output=True,
        text=True
    )
    branch = result.stdout.strip()
    return branch if branch else "main"


def main():
    if not Path(".git").exists():
        print("Erro: este script precisa ser executado dentro de um repositório Git.")
        sys.exit(1)

    commit_msg = input("Digite o nome da commit: ").strip()
    if not commit_msg:
        print("Erro: a mensagem da commit não pode estar vazia.")
        sys.exit(1)

    branch = get_current_branch()

    try:
        print("\nAdicionando arquivos...")
        run(["git", "add", "-A"])

        print("Criando commit...")
        run(["git", "commit", "-m", commit_msg])

        print(f"Sincronizando com o remoto ({branch})...")
        run(["git", "pull", "--rebase", "--autostash", "origin", branch])

        print("Enviando para o GitHub...")
        run(["git", "push", "origin", branch])

        print("\nPronto! Alterações enviadas com sucesso.")
    except subprocess.CalledProcessError:
        print("\nDeu erro em alguma etapa.")
        print("Possíveis causas:")
        print("- houve conflito no rebase")
        print("- o remote tem mudanças novas")
        print("- você precisa resolver conflitos manualmente")
        print("\nTente rodar manualmente:")
        print(f"  git pull --rebase origin {branch}")
        print(f"  git push origin {branch}")
        sys.exit(1)


if __name__ == "__main__":
    main()