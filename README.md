# Pull, Otimização e Avaliação de Prompts com LangChain e LangSmith

Projeto do MBA em IA da Full Cycle. O prompt de baixa qualidade `leonanluppi/bug_to_user_story_v1`, que converte relatos de bugs em User Stories, foi puxado do LangSmith Prompt Hub, otimizado com técnicas de prompt engineering, publicado como `rafaeldaddio/bug_to_user_story_v2` e avaliado com cinco métricas até que todas atingissem 0.8.

O enunciado completo está no [repositório base](https://github.com/devfullcycle/mba-ia-pull-evaluation-prompt).

**Resultado:** o prompt v2 foi aprovado com todas as métricas acima de 0.8 (ver [Resultados Finais](#resultados-finais)).

- Prompt publicado: https://smith.langchain.com/hub/rafaeldaddio/bug_to_user_story_v2
- Dataset de avaliação e experimentos (link público): https://smith.langchain.com/public/495d119d-7e09-4f7b-8d68-41f6c03a2395/d

## Técnicas Aplicadas (Fase 2)

Os avaliadores (`src/metrics.py`) comparam a resposta gerada com a referência do dataset, escrita no padrão "Como um..., eu quero..., para que..." com critérios de aceitação Dado / Quando / Então / E. As técnicas foram escolhidas para reproduzir esse padrão com fidelidade ao relato.

### 1. Role Prompting

**Por quê:** a persona de Product Manager orienta a resposta para o usuário afetado e o valor de negócio, em vez da correção técnica, e dá o tom de uma User Story de backlog.

**Como foi aplicado:**

> Você é um Product Manager sênior, especialista em métodos ágeis. Sua tarefa é transformar relatos de bugs em User Stories claras e testáveis, escritas em português do Brasil.

### 2. Skeleton of Thought

**Por quê:** fixar o esqueleto da resposta garante as seções certas, na ordem certa. A técnica foi preferida ao Chain of Thought porque a resposta é avaliada sem pós-processamento: qualquer raciocínio escrito seria penalizado pela Precision e pela Clarity.

**Como foi aplicado:** o prompt traz o esqueleto da resposta, com as partes a preencher entre « »:

```
Como um «persona específica», eu quero «capacidade desejada», para que «benefício concreto».

Critérios de Aceitação:
- Dado que «contexto inicial»
- Quando «ação ou evento»
- Então «resultado esperado»
- E «complemento verificável»
- E «complemento verificável»
```

Regras complementam o esqueleto com partes condicionais: as seções "Critérios Técnicos:" e "Contexto Técnico:" quando o relato traz a causa ou detalhes técnicos, e grupos de critérios com título por problema quando o relato traz vários problemas.

### 3. Few-shot Learning

**Por quê:** para um modelo de menor porte (`gpt-4.1-mini`), exemplos comunicam formato e nível de detalhe melhor do que instruções, e o formato esperado é rígido.

**Como foi aplicado:** dois exemplos originais, em domínios que não aparecem no dataset, para o modelo não copiar conteúdo: um relato curto e um relato com detalhes técnicos, que demonstra as seções "Critérios Técnicos:" e "Contexto Técnico:". Exemplo do relato curto:

```
<relato>
Na plataforma de cursos, o vídeo da aula sempre recomeça do início, mesmo quando o aluno já assistiu parte dela.
</relato>
<user_story>
Como um aluno assistindo às aulas de um curso online, eu quero que o vídeo retome do ponto em que parei, para que eu possa continuar os estudos sem procurar onde estava.

Critérios de Aceitação:
- Dado que assisti parte de uma videoaula
- Quando volto para a mesma aula
- Então o vídeo deve continuar do ponto em que parei
- E o progresso deve ser salvo automaticamente durante a reprodução
- E a barra de progresso da aula deve mostrar o trecho já assistido
</user_story>
```

## Resultados Finais

### Evidências no LangSmith

O [link público do dataset](https://smith.langchain.com/public/495d119d-7e09-4f7b-8d68-41f6c03a2395/d) dá acesso a:

- o dataset de avaliação `mba-ia-pull-evaluation-prompt-eval`, com os 15 exemplos;
- os experimentos rodados contra ele (a linha de base do v1 e as duas iterações do v2), com as cinco notas de cada exemplo e o comentário de cada avaliador;
- o tracing de cada exemplo: ao clicar em uma linha de um experimento, aparecem a chamada ao modelo (mensagens de sistema e de usuário, resposta e tokens) e as chamadas dos avaliadores.

### Notas

| Prompt | Experimento | Helpfulness | Correctness | F1-Score | Clarity | Precision | Resultado |
|---|---|---|---|---|---|---|---|
| v1 (original) | `leonanluppi-bug_to_user_story_v1-4ac3d9c8` | 0.89 | 0.86 | 0.797 | 0.86 | 0.91 | Reprovado |
| v2, iteração 1 | `rafaeldaddio-bug_to_user_story_v2-facc089a` | 0.86 | 0.88 | 0.86 | 0.82 | 0.89 | Aprovado |
| v2, iteração 2 (final) | `rafaeldaddio-bug_to_user_story_v2-755494bc` | 0.89 | 0.90 | 0.89 | 0.86 | 0.91 | Aprovado |

Todas as avaliações usaram o mesmo dataset, `gpt-4.1-mini` para gerar as respostas e `gpt-4.1` como avaliador, ambos com `temperature=0`. O `evaluate.py` avalia apenas o v2; a linha de base do v1 foi obtida com a mesma função `run_experiment` do script (comando em [Como Executar](#como-executar)).

### Comparação v1 × v2

Com os mesmos modelos e avaliadores, o v1 ficou perto da aprovação e reprovou apenas no F1-Score (0.797). O `gpt-4.1-mini` já conhece o formato de User Story e, mesmo sem instruções, gera respostas razoáveis. A diferença está na forma e no conteúdo: nenhuma resposta do v1 usa critérios Dado / Quando / Então, 12 das 15 usam Markdown (títulos em negrito), algumas incluem itens fora do escopo (como "Testes devem ser realizados para garantir o funcionamento correto do botão") e, no exemplo 15, o resultado é dividido em várias User Stories. O v2 reproduz a estrutura das referências, e o ganho aparece sobretudo no F1-Score:

| Complexidade | F1-Score (v1 → v2) | Clarity (v1 → v2) | Precision (v1 → v2) |
|---|---|---|---|
| Simples (exemplos 1 a 5) | 0.73 → 0.92 | 0.86 → 0.92 | 0.91 → 0.96 |
| Média (exemplos 6 a 12) | 0.82 → 0.86 | 0.89 → 0.83 | 0.94 → 0.90 |
| Complexa (exemplos 13 a 15) | 0.86 → 0.90 | 0.80 → 0.83 | 0.86 → 0.85 |
| Total | 0.80 → 0.89 | 0.86 → 0.86 | 0.91 → 0.91 |

Clarity e Precision ficaram iguais na média: os avaliadores não penalizam o Markdown nem a lista livre de critérios do v1. Nos relatos médios, o v2 ficou um pouco abaixo do v1 nessas duas métricas, principalmente nos exemplos 9 e 11, discutidos na iteração 2. O ganho do v2 está em reproduzir o conteúdo e a estrutura esperados, medidos pelo F1-Score, que era a única métrica reprovada no v1.

O que mudou entre os prompts:

| Aspecto | v1 | v2 | Por quê |
|---|---|---|---|
| Persona | "assistente que ajuda a transformar relatos" | Product Manager sênior, especialista em métodos ágeis | orienta a resposta para o usuário afetado e o valor de negócio |
| Formato | não definido | esqueleto de User Story com critérios Dado / Quando / Então / E | as referências seguem esse padrão, e os avaliadores comparam a resposta com elas |
| Exemplos | nenhum | dois exemplos originais (relato curto e relato com detalhes técnicos) | mostram o formato e o nível de detalhe esperados |
| Relato do bug | enviado duas vezes (system e user) | enviado só na mensagem do usuário | separa as instruções fixas do dado variável |
| Fidelidade | sem regras | usar apenas fatos do relato; marcador entre colchetes para informação faltante | a Precision penaliza informação inventada |
| Seções condicionais | não há | "Critérios Técnicos:" e "Contexto Técnico:" quando o relato traz causa ou detalhes técnicos; grupos com título quando traz vários problemas | as referências dos relatos médios e complexos trazem essas seções |
| Casos especiais | não há | informação faltando, vários problemas no mesmo relato, relato vago | evitam invenção e omissão |
| Saída | livre | texto puro, sem Markdown, começando por "Como um" | evita introduções e comentários que não fazem parte da User Story |

### Iterações

Os números de exemplo abaixo seguem a ordem do arquivo `datasets/bug_to_user_story.jsonl` (simples: 1 a 5; médios: 6 a 12; complexos: 13 a 15). A numeração `[i]` impressa pelo `evaluate.py` segue a ordem em que o LangSmith devolve os resultados, que é diferente.

#### Iteração 1 (commit `f91bb71a` no Hub)

Médias por complexidade do relato:

| Complexidade | F1-Score | Clarity | Precision |
|---|---|---|---|
| Simples (exemplos 1 a 5) | 0.95 | 0.89 | 0.96 |
| Média (exemplos 6 a 12) | 0.79 | 0.83 | 0.86 |
| Complexa (exemplos 13 a 15) | 0.88 | 0.70 | 0.86 |

- **Simples:** respostas próximas das referências; as poucas perdas vêm de critérios complementares que a referência inclui e a resposta não (por exemplo, atualização em tempo real no exemplo 4).
- **Médios:** os avaliadores apontam omissões em relação às referências, que trazem seções complementares (critérios técnicos, de acessibilidade, de prevenção, exemplo de cálculo). No exemplo 7, o modelo usou o limite de timeout do relato (120 segundos) como meta de desempenho.
- **Complexos:** todos os problemas de cada relato foram cobertos, mas a Clarity ficou em 0.70 nos três: os grupos de critérios não têm título por problema, e os avaliadores apontam extensão e repetição entre critérios e contexto.

#### Iteração 2 (commit `2bdc1825` no Hub)

Mudanças no prompt, motivadas pelos comentários dos avaliadores na iteração 1:

- relatos com vários problemas: critérios separados em grupos com título por problema (`A. «Área» - «resultado esperado»:`);
- relatos que indicam a causa técnica: nova seção "Critérios Técnicos:", também demonstrada no exemplo com detalhes técnicos;
- metas de desempenho devem representar o funcionamento correto, e não o limite em que a falha acontece.

Médias por complexidade (iteração 1 → iteração 2):

| Complexidade | F1-Score | Clarity | Precision |
|---|---|---|---|
| Simples (exemplos 1 a 5) | 0.95 → 0.92 | 0.89 → 0.92 | 0.96 → 0.96 |
| Média (exemplos 6 a 12) | 0.79 → 0.86 | 0.83 → 0.83 | 0.86 → 0.90 |
| Complexa (exemplos 13 a 15) | 0.88 → 0.90 | 0.70 → 0.83 | 0.86 → 0.85 |

- **Complexos:** os três passaram a ter grupos com título, e a Clarity subiu de 0.70 para 0.83.
- **Médios:** a seção "Critérios Técnicos:" apareceu nos exemplos 7, 10 e 12, justamente os que mais melhoraram (no 7, o F1 foi de 0.70 para 1.00, já com uma meta de desempenho adequada). As quedas ficaram nos exemplos 9 e 11, onde nenhuma seção nova apareceu: no 9, a resposta perdeu o contexto com os valores do cálculo; no 11, priorizou impedir a adição ao carrinho e omitiu a validação de estoque no checkout.
- **Simples:** nenhuma regra nova se aplica a eles, e ainda assim as notas variaram até 0.11 por exemplo e até 0.03 na média do grupo. Essa é a ordem de grandeza da variação entre execuções, causada pela mudança no prompt e pelo próprio avaliador.

### Por que o processo parou na iteração 2

Na iteração 2, todas as métricas ficaram em 0.86 ou mais, e cada mudança produziu o efeito previsto, acima da variação entre execuções. As omissões restantes estão em conteúdos que as referências trazem sem base no relato, como a reserva de estoque por 15 minutos no exemplo 11 ou o e-mail de confirmação no exemplo 6. Incluí-los ajustaria o prompt a estas 15 respostas específicas, em vez de melhorar a conversão de bugs em User Stories.

## Como Executar

### Pré-requisitos

- Python 3.10 ou superior (o projeto foi executado com Python 3.11).
- Conta no [LangSmith](https://smith.langchain.com) com uma API key e um handle público no Prompt Hub. O handle é criado ao tornar um prompt público pela primeira vez (Prompts → menu de três pontos ao lado de Playground → Make Public) e não pode ser alterado depois.
- API key da OpenAI (o projeto também suporta Google Gemini).

### Instalação

```bash
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows
pip install -r requirements.txt
```

### Configuração

Copie `.env.example` para `.env` e preencha:

| Variável | Descrição | Valor usado neste projeto |
|---|---|---|
| `LANGSMITH_API_KEY` | API key do LangSmith | (chave pessoal) |
| `LANGSMITH_PROJECT` | projeto de tracing; também define o nome do dataset (`<projeto>-eval`) | `mba-ia-pull-evaluation-prompt` |
| `USERNAME_LANGSMITH_HUB` | handle público no Prompt Hub | `rafaeldaddio` |
| `LLM_PROVIDER` | `openai` ou `google` | `openai` |
| `OPENAI_API_KEY` | API key da OpenAI (ou `GOOGLE_API_KEY`, para Gemini) | (chave pessoal) |
| `LLM_MODEL` | modelo que gera as respostas | `gpt-4.1-mini` |
| `EVAL_MODEL` | modelo avaliador | `gpt-4.1` |

Sobre os modelos: a avaliação usa `temperature=0`, e a família GPT-4.1 aceita esse valor na configuração do projeto. Na família GPT-5, o `langchain-openai` descarta a temperatura sem aviso; na família GPT-6, a API não aceita temperatura com o esforço de raciocínio padrão. A OpenAI programou a remoção dos modelos GPT-4.1 da API para 14/01/2027; depois dessa data será preciso escolher outros modelos, e as notas podem variar.

### Execução

Todos os comandos são executados na raiz do repositório, com o ambiente virtual ativo.

1. **Pull do prompt original:** `python src/pull_prompts.py` salva `leonanluppi/bug_to_user_story_v1` em `prompts/bug_to_user_story_v1.yml`.
2. **Otimização:** edição de `prompts/bug_to_user_story_v2.yml`.
3. **Push:** `python src/push_prompts.py` valida o YAML e publica `{USERNAME_LANGSMITH_HUB}/bug_to_user_story_v2` como prompt público, com descrição, tags e técnicas aplicadas.
4. **Avaliação:** `python src/evaluate.py` cria (ou reaproveita) o dataset, roda o experimento e imprime as notas e o link. São cerca de 60 chamadas de LLM por rodada, com custo estimado em US$ 0.25 usando os modelos acima.
5. **Testes:** `pytest tests/test_prompts.py` roda os 6 testes de validação do prompt v2.

Linha de base do v1 (opcional), com as mesmas funções do `evaluate.py`:

```bash
python -c "import sys; sys.path.insert(0, 'src'); import evaluate; from langsmith import Client; s, _ = evaluate.run_experiment(Client(), 'leonanluppi/bug_to_user_story_v1', 'mba-ia-pull-evaluation-prompt-eval'); evaluate.display_results('leonanluppi/bug_to_user_story_v1', s)"
```

Link público do dataset (executar uma única vez, porque cada nova chamada gera outro link):

```bash
python -c "from dotenv import load_dotenv; load_dotenv('.env'); from langsmith import Client; print(Client().share_dataset(dataset_name='mba-ia-pull-evaluation-prompt-eval')['url'])"
```

Para consultar o link já criado sem alterá-lo, use `read_dataset_shared_schema` no lugar de `share_dataset`.
