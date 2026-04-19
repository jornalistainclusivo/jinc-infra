"""JINC Scripts — Ponto de entrada para automação e migração."""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _check_env() -> None:
    """Valida variáveis de ambiente obrigatórias antes de qualquer execução."""
    required = ["STRAPI_TOKEN"]
    missing = [var for var in required if not os.getenv(var)]
    if missing:
        print(f"❌ Variáveis ausentes: {', '.join(missing)}")
        print("   Copie scripts/.env.example → scripts/.env e preencha.")
        sys.exit(1)


def main() -> None:
    _check_env()

    from tools.strapi_client import StrapiClient

    client = StrapiClient()
    print(f"✅ Conectado: {client.base_url}")
    print("   Use 'from tools.strapi_client import StrapiClient' nos seus scripts.")


if __name__ == "__main__":
    main()
