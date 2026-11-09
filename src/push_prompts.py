"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)
"""

import os
import sys

from dotenv import load_dotenv
from langsmith import Client
from langsmith.utils import LangSmithConflictError
from langchain_core.prompts import ChatPromptTemplate
from utils import load_yaml, check_env_vars, print_section_header, validate_prompt_structure

load_dotenv()

PROMPT_FILE = "prompts/bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"
EXPECTED_VARIABLES = ["bug_report"]


def build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta o ChatPromptTemplate (system + user) a partir dos dados do YAML."""
    return ChatPromptTemplate.from_messages([
        ("system", prompt_data["system_prompt"]),
        ("user", prompt_data["user_prompt"]),
    ])


def build_readme(prompt_data: dict) -> str:
    """Gera o readme exibido na página do prompt no Hub."""
    techniques = "\n".join(f"- {t}" for t in prompt_data.get("techniques_applied", []))
    return (
        f"# {PROMPT_KEY}\n\n"
        f"{prompt_data['description']}\n\n"
        f"- Versão: {prompt_data['version']}\n"
        f"- Baseado em: {prompt_data.get('based_on', '-')}\n"
        f"- Variável de entrada: `{EXPECTED_VARIABLES[0]}`\n\n"
        f"## Técnicas aplicadas\n\n{techniques}\n"
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Identificador completo do prompt ("handle/nome")
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    client = Client()

    print(f"Publicando {prompt_name} no LangSmith Hub...")

    try:
        url = client.push_prompt(
            prompt_name,
            object=build_chat_prompt(prompt_data),
            is_public=True,
            description=prompt_data["description"],
            readme=build_readme(prompt_data),
            tags=prompt_data.get("tags", []),
        )
    except LangSmithConflictError as e:
        print("   ✓ Conteúdo idêntico à versão mais recente no Hub: nenhum commit novo criado")
        print(f"     ({e})")
        return True

    print(f"   ✓ Prompt publicado: {url}")
    return True


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Além das regras de utils.validate_prompt_structure (campos obrigatórios,
    ausência de TODO e mínimo de 2 técnicas), confere que existe user_prompt e
    que o template tem exatamente a variável {bug_report}. Chaves soltas no texto
    seriam interpretadas como variáveis e quebrariam a avaliação.

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    _, errors = validate_prompt_structure(prompt_data)

    if not str(prompt_data.get("user_prompt", "")).strip():
        errors.append("user_prompt está vazio ou ausente")
        return (False, errors)

    try:
        variables = sorted(build_chat_prompt(prompt_data).input_variables)
    except Exception as e:
        errors.append(f"Template inválido: {e}")
        return (False, errors)

    if variables != EXPECTED_VARIABLES:
        errors.append(f"Variáveis do template devem ser {EXPECTED_VARIABLES}, encontradas: {variables}")

    return (len(errors) == 0, errors)


def main():
    """Função principal"""
    print_section_header("PUSH DE PROMPTS PARA O LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY", "USERNAME_LANGSMITH_HUB"]):
        return 1

    data = load_yaml(PROMPT_FILE)
    if not data or PROMPT_KEY not in data:
        print(f"❌ Chave '{PROMPT_KEY}' não encontrada em {PROMPT_FILE}")
        return 1
    prompt_data = data[PROMPT_KEY]

    is_valid, errors = validate_prompt(prompt_data)
    if not is_valid:
        print("❌ Prompt inválido:")
        for error in errors:
            print(f"   - {error}")
        return 1
    print(f"✓ {PROMPT_FILE} validado")

    prompt_name = f"{os.getenv('USERNAME_LANGSMITH_HUB')}/{PROMPT_KEY}"

    try:
        success = push_prompt_to_langsmith(prompt_name, prompt_data)
    except Exception as e:
        print(f"❌ Falha no push de {prompt_name}: {e}")
        print("\nVerifique LANGSMITH_API_KEY e se USERNAME_LANGSMITH_HUB é o handle do seu workspace.")
        return 1

    if success:
        print("\n✅ Push concluído.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
