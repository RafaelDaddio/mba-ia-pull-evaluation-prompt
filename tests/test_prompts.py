"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
from pathlib import Path

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt():
    """Dados do prompt v2 (conteúdo sob a chave raiz do YAML)."""
    return load_prompts(PROMPT_FILE)[PROMPT_KEY]


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt
        assert prompt["system_prompt"].strip()

    def test_prompt_has_role_definition(self, prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert "Você é um Product Manager" in prompt["system_prompt"]

    def test_prompt_mentions_format(self, prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        system_prompt = prompt["system_prompt"]
        for part in ("Como um", "eu quero", "para que", "Critérios de Aceitação:"):
            assert part in system_prompt, f"Formato de User Story sem '{part}'"

    def test_prompt_has_few_shot_examples(self, prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(
            r"<relato>(.+?)</relato>\s*<user_story>(.+?)</user_story>",
            prompt["system_prompt"],
            re.DOTALL,
        )
        assert len(examples) >= 2, "Few-shot exige ao menos 2 pares de entrada/saída"
        for _, output in examples:
            assert output.strip().startswith("Como um")
            assert "Critérios de Aceitação:" in output

    def test_prompt_no_todos(self):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        assert "TODO" not in PROMPT_FILE.read_text(encoding="utf-8")

    def test_minimum_techniques(self, prompt):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        assert len(prompt.get("techniques_applied", [])) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
