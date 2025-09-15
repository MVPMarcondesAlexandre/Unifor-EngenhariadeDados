# 📘 **Roteiro de Atividade Dirigida de Engenharia de Dados**  
Usando **Amazon AWS**

---

## 📂 **1. Datasets Públicos**

### 🔹 **INMET (Clima)**  
Dados históricos meteorológicos.  

🔗 Link direto (ZIP com CSV):  
- Dados Históricos INMET 2022  
- Dados Históricos INMET 2023  

### 🔹 **ANP (Combustíveis)**  
Preços semanais de combustíveis (Etanol + Gasolina Comum - Maio/2025, Junho/2025 e Julho/2025).  

🔗 Link direto (dados.gov.br):  
- CSV Completo ANP  

---

## 📂 **2. Estrutura Medalhão no S3**

- `br-medalhao-bronze` → dados brutos  
- `br-medalhao-silver` → dados tratados e normalizados (Parquet)  
- `br-medalhao-gold` → dados analíticos integrados  

---

### 🔹 **2.1 — Criando Buckets no S3**

📌 Via **AWS CLI (Bash):**
```bash
aws s3 mb s3://br-medalhao-bronze
aws s3 mb s3://br-medalhao-silver
aws s3 mb s3://br-medalhao-gold
```

📌 Pelo **Console da AWS**:

1. Acesse Amazon S3 no console.
2. Clique em **Create bucket**.
3. Nomeie como `br-medalhao-bronze` e configure região e permissões conforme políticas da sua turma.
4. Repita para `br-medalhao-silver` e `br-medalhao-gold`.

---

### 🔹 **2.2 — Ingestão dos Datasets (Bronze)**

📌 **INMET (Clima): Baixar e enviar para o S3**

```bash
# exemplo para 2022
wget https://portal.inmet.gov.br/uploads/dadoshistoricos/2022.zip -O inmet_2022.zip
unzip inmet_2022.zip -d inmet_2022

# copia recursiva para o bucket Bronze
aws s3 cp inmet_2022/ s3://br-medalhao-bronze/inmet/ --recursive
```

📌 **Console**:

* Baixe e descompacte `inmet_2022.zip` localmente.
* Acesse o bucket `br-medalhao-bronze`.
* Clique em **Upload** → selecione a pasta `inmet_2022`.

📌 **ANP (Combustíveis):**

```bash
wget https://distribuicaodecombustiveis.dados.gov.br/arquivos/precos-semanais/anp-precos-semanais.csv -O combustiveis.csv
aws s3 cp combustiveis.csv s3://br-medalhao-bronze/anp/
```

---

### 🔹 **2.3 — Camada Silver**

🎯 Objetivo: converter para **Parquet**, padronizar colunas (`data`, `temp_max`, `preco_medio`) e criar colunas auxiliares `ano` e `semana` para facilitar o join semanal.

📌 Criar **IAM Role** para o Glue:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:ListBucket"],
      "Resource": [
        "arn:aws:s3:::br-medalhao-bronze",
        "arn:aws:s3:::br-medalhao-silver",
        "arn:aws:s3:::br-medalhao-gold"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject"],
      "Resource": [
        "arn:aws:s3:::br-medalhao-bronze/*",
        "arn:aws:s3:::br-medalhao-silver/*",
        "arn:aws:s3:::br-medalhao-gold/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": ["glue:*","cloudwatch:PutMetricData","logs:*"],
      "Resource": "*"
    }
  ]
}
```

📌 Criar Glue Job via CLI:

```bash
aws glue create-job   --name silver-transform   --role <GLUE_IAM_ROLE>   --command '{"Name":"glueetl","ScriptLocation":"s3://br-medalhao-bronze/scripts/silver_transform.py"}'
```

---

### 🔹 **2.4 — Camada Gold: Criar tabela analítica unificada**

🎯 Objetivo: tabela semanal integrando clima (INMET) e preço (ANP).

📌 **Athena (Bash):**

```bash
aws athena start-query-execution  --query-string "CREATE TABLE gold_mobilidade AS
 SELECT s.linha, s.horario, i.temp_max, a.preco_medio
 FROM silver_sptrans s
 LEFT JOIN silver_inmet i ON date(s.horario)=i.data
 LEFT JOIN silver_anp a ON weekofyear(s.horario)=a.semana;"  --result-configuration OutputLocation=s3://br-medalhao-gold/queries/
```

📌 **Console**:

* Vá em Athena → Editor
* Selecione `br_medalhao_db`
* Rode a query acima
* Saída salva em `br-medalhao-gold/queries/`

---

### 🔹 **2.5 — Visualização (QuickSight)**

* Conectar ao Glue Catalog (tabela `gold_mobilidade`).
* Criar dashboards:

  * Passageiros transportados vs. temperatura
  * Preço médio de combustível vs. mobilidade
  * Tendência semanal

---

### 🔹 **2.6 — Orquestração (Step Functions)**

Pipeline:

1. Lambda → SPTrans API  
2. Glue Job → Silver  
3. Athena → Gold  
4. QuickSight → Dashboard atualizado  

Pode ser criado tanto via **Console (drag and drop)** quanto via **Bash (JSON de definição do fluxo)**.
