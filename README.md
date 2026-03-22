# 🚀 JINC Rebuild - Infraestrutura & Orquestração

Este é o repositório central de orquestração do ecossistema **Jornalista Inclusivo**. Aqui gerenciamos a infraestrutura, os scripts de migração e a harmonia entre o CMS e o Frontend.

## 🏗️ Arquitetura

O projeto é baseado em microserviços isolados via Docker:

- **CMS:** Strapi 5 (Node.js 20 + SQLite) - Porta `1337`
- **Frontend:** Next.js (App Router) - Porta `3000`

## 🛠️ Pré-requisitos

- Docker & Docker Compose
- Node.js 20+ (para desenvolvimento local fora do container)

## 🚦 Como Rodar o Ambiente Completo

1. **Clone os Submódulos (se aplicável) ou Garanta as Pastas:**
    Certifique-se de que as pastas `cms/` e `jinc-frontend/` possuem seus respectivos códigos.

2. **Configuração de Ambiente:**
    Crie ou ajuste o arquivo `.env` na raiz (baseado no `.env.example`).

3. **Subir os Containers:**

    ```bash
    docker-compose up --build -d
    ```

4. **Acesso:**
    - **Painel Administrativo (Strapi):** [http://localhost:1337/admin](http://localhost:1337/admin)
    - **Site (Next.js):** [http://localhost:3000](http://localhost:3000)

## 🚛 Migração de Dados

A pasta `/scripts` contém as ferramentas em Python para extração do banco MariaDB (WordPress) e injeção via API no Strapi 5, garantindo a preservação da camada de contexto (`Contextual_Layer`).

---
> **Nota de Acessibilidade:** Este projeto segue rigorosamente os padrões WCAG 2.2 e a LBI, garantindo que a informação seja democratizada para todos os usuários.
