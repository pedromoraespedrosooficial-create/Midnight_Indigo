#  Midnight Indigo

**Midnight Indigo: Uma plataforma de e-commerce de luxo.**
Desenvolvida com Python (Flask) e SQL Server. Inclui painel de admin, sistema de vendedores, carrinho de compras com recomendações e cupons.

> **Status:**  Em Desenvolvimento (Funcional) 

Este projeto simula um marketplace real, permitindo que diferentes vendedores gerenciem seus próprios produtos, enquanto os administradores supervisionam o site, cupons e pedidos.

---

##  Funcionalidades

* **Três Níveis de Usuário:** Sistema de autenticação completo (Cliente, Vendedor, Admin) com permissões distintas.
* **Painel de Admin:** CRUD completo para Usuários, Produtos (todos), Cupons e visualização de Pedidos.
* **Painel de Vendedor:** Vendedores podem gerenciar (CRUD) apenas os *seus* produtos.
* **Catálogo de Produtos:** Página de catálogo com filtros de categoria dinâmicos.
* **Sliders na Home:** A página inicial exibe produtos em carrosséis (Novidades, Mais Vendidos, Relógios, Destaques).
* **Carrinho de Compras:** Funcionalidade completa de Adicionar, Remover e Atualizar Quantidade.
* **Sistema de Cupons:** Aplicação de descontos por valor fixo (R$) ou porcentagem (%).
* **Sistema de Recomendação:** Sugestões de produtos (cross-sell) na página do carrinho, baseadas nas categorias dos itens atuais.
* **Formatação de Moeda:** Um filtro Jinja2 personalizado (`| currency`) formata todos os valores monetários para o padrão brasileiro (ex: `R$ 25.000.000,00`).

---

## 🔧 Tecnologias Utilizadas

* **Backend:** Python 3.10+
* **Framework:** Flask
* **Banco de Dados:** Microsoft SQL Server
* **Driver DB:** `pyodbc`
* **ORM:** SQLAlchemy
* **Autenticação:** Flask-Login, Flask-Bcrypt
* **Templates:** Jinja2
* **Frontend:** HTML5, CSS3 (com Flexbox/Grid), JavaScript (básico)
* **Variáveis de Ambiente:** `python-dotenv`

---

## ⚙️ Como Rodar o Projeto

### 1. Pré-requisitos

* Python 3.10 ou superior
* Microsoft SQL Server (com o [Driver ODBC 17](https://learn.microsoft.com/pt-br/sql/connect/odbc/download-odbc-driver-for-sql-server))
* SQL Server Management Studio (SSMS)

### 2. Clonar o Repositório

```bash
git clone [https://github.com/seu-usuario/midnight-indigo.git](https://github.com/seu-usuario/midnight-indigo.git)
cd midnight-indigo
3. Ambiente Virtual e Dependências
Crie e ative um ambiente virtual:

Bash

python -m venv venv
# Windows
.\venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
Instale as dependências:

Bash

pip install -r requirements.txt
4. Configuração do Banco de Dados
Abra o SSMS e crie um novo banco de dados. (Ex: Midnight_Indigo_DB).

Crie um arquivo .env na raiz do projeto.

Adicione suas variáveis de ambiente ao .env. (Use o .env.example como base).

.env (Exemplo):

SECRET_KEY=sua_chave_secreta_super_segura_aqui
DATABASE_URL=mssql+pyodbc://USUARIO:SENHA@SERVIDOR/Midnight_Indigo_DB?driver=ODBC+Driver+17+for+SQL+Server
(Substitua USUARIO, SENHA e SERVIDOR pelas suas credenciais do SQL Server)

5. Criar as Tabelas e Usuários
Com o banco criado e o .env configurado, rode o script create_db.py uma vez para inicializar o banco de dados:

Bash

python create_db.py
Isso criará todas as tabelas e os usuários padrão:

Admin: admin@midnight.com / admin123

Vendedor: vendedor@midnight.com / vendedor123

6. (Opcional) Popular o Banco
Para adicionar os produtos de luxo de exemplo, execute o script SQL (insert_produtos.sql ou similar) diretamente no seu SSMS, apontado para o banco Midnight_Indigo_DB.

7. Rodar a Aplicação
Finalmente, inicie o servidor Flask:

Bash

python app.py
Acesse http://127.0.0.1:5000 no seu navegador.

Licença
Este projeto é distribuído sob a licença MIT.