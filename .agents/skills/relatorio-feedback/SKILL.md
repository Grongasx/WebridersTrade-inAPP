---
name: relatorio-feedback
description: Skill para apresentação de relatório final de feedback das execuções, incluindo alterações realizadas, status, métricas do grafo de código e estimativa de consumo de tokens.
---

# Skill: Relatório de Feedback Final (`relatorio-feedback`)

Esta skill estabelece a estrutura padronizada de feedback ao concluir comandos e tarefas no **Vale Presente Manager**.

## Estrutura do Relatório Final

Ao finalizar uma tarefa, apresentar o resumo compacto contendo as seções abaixo:

```markdown
### 📊 Relatório Final de Execução

1. **Ações Realizadas**:
   - Resumo direto das alterações efetuadas nos arquivos.

2. **Status da Aplicação**:
   - Status da compilação/testes (`python -m py_compile main.py`).
   - Versão registrada em [CHANGELOG.md](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/CHANGELOG.md).
   - Status do Git (Commit & Push).

3. **Métricas de Código (Code Review Graph)**:
   - Nós e arestas analisados / atualizados.
   - Economia de contexto estimada (em %).

4. **Consumo e Estimativa de Tokens**:
   - **Tokens de Entrada (Prompt)**: Ex: ~12.5k tokens.
   - **Tokens de Saída (Completion)**: Ex: ~1.2k tokens.
   - **Economia pelo Grafo Local**: Redução média de até 99% de leituras desnecessárias.
```
