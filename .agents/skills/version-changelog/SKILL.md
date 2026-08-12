---
name: version-changelog
description: Gerenciamento e documentação de versões e histórico de alterações (Changelog) do Vale Presente Manager.
---

# Skill: Version Changelog Manager (`version-changelog`)

Esta skill orienta a documentação ultra-resumida de alterações no arquivo [CHANGELOG.md](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/CHANGELOG.md) seguindo Versionamento Semântico (`MAJOR.MINOR.PATCH`).

## Regras de Versionamento

- **`MAJOR` (x.0.0)**: Mudança grande ou estrutural no sistema.
- **`MINOR` (1.x.0)**: Atualização média ou nova funcionalidade.
- **`PATCH` (1.0.x)**: Pequeno ajuste, correção de bug ou hotfix.

## Formato Padrão do `CHANGELOG.md`

```markdown
# Histórico de Versões - Vale Presente Manager

## [1.0.0] - Versão Inicial
- Lançamento inicial do sistema.
- Cadastro de clientes, vales e outlet.
- Impressão de etiquetas 3 colunas.
- Banco de dados PostgreSQL (Neon).
```

## Como Registrar Novas Alterações

1. Abra o arquivo [CHANGELOG.md](file:///c:/Users/Latitude/OneDrive/%C3%81rea%20de%20Trabalho/Projetos%20Pessoais/vale_presente_manager/CHANGELOG.md).
2. Adicione o novo bloco de versão no topo da lista.
3. Descreva cada alteração em 1 linha objetiva.
