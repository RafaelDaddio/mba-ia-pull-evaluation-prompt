"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull do prompt semente do desafio (leonanluppi/bug_to_user_story_v1),
   fixando o commit lido para que o hash registrado corresponda ao conteúdo salvo
3. Converte as mensagens do ChatPromptTemplate em system_prompt / user_prompt
4. Salva localmente em prompts/bug_to_user_story_v1.yml e confere o arquivo gravado

Sobre `dangerously_pull_public_prompt=True`: o LangSmith bloqueia por padrão o
pull de prompts identificados por "owner/nome", porque um prompt do Hub é um
objeto LangChain serializado e pode vir de terceiros. Aqui o prompt é o semente
do desafio, então o risco é conhecido e aceito.
"""

import sys
from pathlib import Path

import yaml
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
)
from utils import save_yaml, load_yaml, check_env_vars, print_section_header

load_dotenv()

SOURCE_PROMPT = "leonanluppi/bug_to_user_story_v1"
OUTPUT_PATH = Path("prompts/bug_to_user_story_v1.yml")
PROMPT_KEY = "bug_to_user_story_v1"
VERSION = "v1"

# O prompt semente não tem descrição nem tags no Hub (só a tag automática
# "ChatPromptTemplate"), então esses metadados são definidos aqui.
DEFAULT_DESCRIPTION = "Prompt para converter relatos de bugs em User Stories"
DEFAULT_TAGS = ["bug-analysis", "user-story", "product-management"]

# Tipo de cada mensagem do template -> campo correspondente no YAML
MESSAGE_FIELDS = {
    SystemMessagePromptTemplate: "system_prompt",
    HumanMessagePromptTemplate: "user_prompt",
}


def _represent_str(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
    """Grava textos com quebra de linha no estilo bloco (|), mantendo o prompt legível."""
    style = "|" if "\n" in data else None
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style=style)


def extract_messages(prompt: ChatPromptTemplate) -> dict:
    """
    Converte as mensagens do ChatPromptTemplate em {"system_prompt", "user_prompt"}.

    Falha explicitamente diante de estruturas que o YAML do projeto não representa
    (mensagens de outros papéis, placeholders, conteúdo multimodal ou papéis repetidos).
    """
    if not isinstance(prompt, ChatPromptTemplate):
        raise TypeError(f"Esperado ChatPromptTemplate, recebido {type(prompt).__name__}")

    fields = {}
    for message in prompt.messages:
        field = MESSAGE_FIELDS.get(type(message))
        if field is None:
            raise ValueError(f"Tipo de mensagem não suportado: {type(message).__name__}")
        if not isinstance(message.prompt, PromptTemplate):
            raise ValueError(f"Conteúdo não textual na mensagem de {field}")
        if field in fields:
            raise ValueError(f"Mais de uma mensagem mapeada para {field}")
        fields[field] = message.prompt.template

    if "system_prompt" not in fields:
        raise ValueError("O prompt não tem mensagem de sistema")

    return fields


def pull_prompts_from_langsmith(output_path: Path = OUTPUT_PATH) -> bool:
    """
    Faz pull do prompt semente e o salva em YAML.

    Args:
        output_path: Caminho do arquivo .yml de saída

    Returns:
        True se o arquivo foi gravado e confere com o Hub, False caso contrário
    """
    client = Client()

    print(f"Puxando {SOURCE_PROMPT} do LangSmith Hub...")

    # Primeiro descobre o commit mais recente; depois puxa o template fixado
    # nesse commit, para que conteúdo e hash venham da mesma versão.
    commit = client.pull_prompt_commit(SOURCE_PROMPT, dangerously_pull_public_prompt=True)
    prompt = client.pull_prompt(
        f"{SOURCE_PROMPT}:{commit.commit_hash}",
        dangerously_pull_public_prompt=True,
    )
    repo = client.get_prompt(SOURCE_PROMPT)

    print(f"   ✓ Commit: {commit.commit_hash[:12]}")
    print(f"   ✓ Variáveis de entrada: {prompt.input_variables}")

    messages = extract_messages(prompt)

    data = {
        PROMPT_KEY: {
            "description": (repo.description if repo and repo.description else DEFAULT_DESCRIPTION),
            **messages,
            "version": VERSION,
            "created_at": repo.created_at.date().isoformat() if repo else None,
            "tags": DEFAULT_TAGS,
            "source": SOURCE_PROMPT,
            "commit_hash": commit.commit_hash,
        }
    }

    yaml.add_representer(str, _represent_str)
    if not save_yaml(data, str(output_path)):
        return False

    # Relê o arquivo e compara com o que veio do Hub: garante que a serialização
    # YAML não alterou nenhum caractere do prompt.
    saved = (load_yaml(str(output_path)) or {}).get(PROMPT_KEY, {})
    divergent = [field for field, text in messages.items() if saved.get(field) != text]
    if divergent:
        print(f"❌ Conteúdo gravado diverge do Hub em: {', '.join(divergent)}")
        return False

    print(f"   ✓ Salvo em {output_path} ({', '.join(messages)})")
    return True


def main():
    """Função principal"""
    print_section_header("PULL DE PROMPTS DO LANGSMITH HUB")

    if not check_env_vars(["LANGSMITH_API_KEY"]):
        return 1

    try:
        success = pull_prompts_from_langsmith()
    except Exception as e:
        print(f"❌ Falha no pull de {SOURCE_PROMPT}: {e}")
        print("\nVerifique LANGSMITH_API_KEY e LANGSMITH_ENDPOINT no .env e sua conexão.")
        return 1

    if success:
        print("\n✅ Pull concluído.")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
