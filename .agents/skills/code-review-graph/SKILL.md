---
name: code-review-graph
description: Grafo de inteligência de código local (code-review-graph). Atualizações incrementais, análise de impacto, código morto e arquitetura.
---

# Skill: Code Review Graph (`code-review-graph`)

Esta skill orienta o uso da ferramenta `code-review-graph` integrada ao projeto.

## Comandos Principais

1. **Construir / Re-indexar Grafo**:
   ```bash
   python -m code_review_graph build
   ```

2. **Atualização Incremental**:
   ```bash
   python -m code_review_graph update
   ```

3. **Verificar Status do Grafo**:
   ```bash
   python -m code_review_graph status
   ```

4. **Análise de Arquitetura e Acoplamento**:
   ```bash
   python -m code_review_graph architecture
   ```

5. **Análise de Impacto de Alterações**:
   ```bash
   python -m code_review_graph impact
   ```

6. **Detecção de Código Morto**:
   ```bash
   python -m code_review_graph dead-code
   ```
