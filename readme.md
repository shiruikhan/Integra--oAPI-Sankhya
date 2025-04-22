
# 🔄 Integração Automática Sankhya ↔ MySQL

Automatize a integração entre banco de dados MySQL e a API do ERP Sankhya com este conjunto de scripts Python. O projeto executa de forma sequencial o envio e recebimento de dados, estruturado em módulos claros e com fácil configuração via `.env`.

---

## 📦 Estrutura do Projeto

```
📁 TGSCAB.py     # Integra cabeçalhos dos pedidos
📁 TGSPAR.py     # Integra os parceiros envolvidos
📁 TGSITE.py     # Integra itens do pedido
📁 TGSSER.py     # Integra números de série por item
📁 launcher.bat  # Script para execução automatizada
```

---

## ⚙️ Tecnologias

- Python 3.9+
- MySQL Connector
- Requests
- Sankhya API
- Dotenv

---

## 🚀 Como usar

1. Clone o repositório:

```bash
git clone https://github.com/seu-usuario/nome-do-repo.git
cd nome-do-repo
```

2. Crie um arquivo `.env` com as seguintes variáveis:

```dotenv
MYSQL_HOST=...
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=...

SANKHYA_AUTH_URL=...
SANKHYA_API_URL=...
SANKHYA_APP_KEY=...
SANKHYA_AUTH_TOKEN=...
SANKHYA_USERNAME=...
SANKHYA_PASSWORD=...
```

3. Execute o script desejado manualmente:

```bash
python TGSCAB.py
```

Ou utilize o `launcher.bat` para rodar todos em sequência (Windows):

```bash
launcher.bat
```

---

## 🧠 Lógica de Integração

Cada script:

- Conecta ao MySQL
- Consulta registros pendentes
- Envia dados para a API Sankhya
- Atualiza os registros como “integrados”

Todos os pontos de falha são tratados com mensagens claras no terminal.

---

## 📋 Checklist

✅ Modularização clara  
✅ Tratamento de exceções  
✅ Integração segura com `.env`  
✅ Compatível com ambientes automatizados