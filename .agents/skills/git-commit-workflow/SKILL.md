---
name: git-commit-workflow
description: Fluxo de verificação e commit Git automático após validação de funcionamento perfeito e atualização do CHANGELOG.md.
---

# Skill: Git Commit Workflow (`git-commit-workflow`)

Esta skill estabelece a rotina de validação e criação de commits Git no repositório.

## Passos para o Commit

1. **Verificação de Compilação/Sintaxe**:
   ```bash
   python -m py_compile main.py
   ```

2. **Atualização do Grafo de Código**:
   ```bash
   python -m code_review_graph update
   ```

3. **Atualização do CHANGELOG.md**:
   - Garantir que a versão e itens foram incrementados em [CHANGELOG.md](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/CHANGELOG.md).

4. **Execução do Commit**:
   ```bash
   git add .
   git commit -m "feat(v1.0.1): descrição resumida da atualização"
   ```
