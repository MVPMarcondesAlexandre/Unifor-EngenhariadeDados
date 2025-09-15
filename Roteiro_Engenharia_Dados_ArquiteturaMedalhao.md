Roteiro de Atividade Dirigida de Engenharia de Dados
usando Amazon AWS

1.  Datasets Públicos

INMET (Clima)

Dados históricos meteorológicos.

Link direto (ZIP com CSV):

ANP (Combustíveis)

Preços semanais de combustíveis (Etanol + Gasolina Comum - Maio/2025, Junho/2025 e Julho/2025)

Link direto (dados.gov.br):

2. Estrutura Medalhão no S3

br-medalhao-bronze → dados brutos

br-medalhao-silver → dados tratados e normalizados (Parquet)

br-medalhao-gold → dados analíticos integrados

2.1 — Criando Buckets no S3

Via AWS CLI (Bash)

aws s3 mb s3://br-medalhao-bronze

aws s3 mb s3://br-medalhao-silver

aws s3 mb s3://br-medalhao-gold

Pelo Console da AWS

Acesse Amazon S3 no console.

Clique em Create bucket.

Nomeie como br-medalhao-bronze. Configure região e permissões conforme políticas da sua turma.

Repita para br-medalhao-silver e br-medalhao-gold.

2.2 — Ingestão dos Datasets (Bronze)

INMET (Clima): Baixar e enviar para o S3.

Bash

# exemplo para 2022

wget https://portal.inmet.gov.br/uploads/dadoshistoricos/2022.zip -O inmet_2022.zip

unzip inmet_2022.zip -d inmet_2022

# copia recursiva para o bucket Bronze

aws s3 cp inmet_2022/ s3://br-medalhao-bronze/inmet/ --recursive

Console

Baixe e descompacte inmet_2022.zip localmente.

Acesse o bucket br-medalhao-bronze.

Clique em Upload.

Faça upload da pasta inmet_2022.

ANP (Combustíveis): Baixar CSV e enviar.

Bash

wget https://distribuicaodecombustiveis.dados.gov.br/arquivos/precos-semanais/anp-precos-semanais.csv -O combustiveis.csv

aws s3 cp combustiveis.csv s3://br-medalhao-bronze/anp/

Console

Baixe o arquivo CSV no PC.

Acesse br-medalhao-bronze/anp/.

Clique em Upload → selecione combustiveis.csv.

2. 3 — Camada Silver

Objetivo: converter para Parquet, padronizar colunas (data, temp_max, preco_medio) e criar colunas auxiliares ano e semana para facilitar o join semanal.

  No Console AWS, abra IAM → Roles → Create role. Selecione Entidade Confiável: Serviço AWS → Caso de uso Glue (ou "Glue" / "Glue - AWS Glue"). Clique Next.

Políticas de Permissões:

Recomendo criar/usar uma policy customizada com permissões S3 apenas para seus buckets. Exemplo (opcional: cole no editor JSON ao criar policy e anexe aqui):

{

"Version": "2012-10-17",

"Statement": [

{

"Effect": "Allow",

"Action": [

"s3:ListBucket"

],

"Resource": [

"arn:aws:s3:::br-medalhao-bronze",

"arn:aws:s3:::br-medalhao-silver",

"arn:aws:s3:::br-medalhao-gold"

]

},

{

"Effect": "Allow",

"Action": [

"s3:GetObject",

"s3:PutObject",

"s3:DeleteObject"

],

"Resource": [

"arn:aws:s3:::br-medalhao-bronze/*",

"arn:aws:s3:::br-medalhao-silver/*",

"arn:aws:s3:::br-medalhao-gold/*"

]

},

{

"Effect": "Allow",

"Action": [

"glue:*",

"cloudwatch:PutMetricData",

"logs:*"

],

"Resource": "*"

}

]

}

Dê um nome à role, ex.: glue-silver-role-br-medalhao, finalize.

Observação: você pode também anexar as managed policies AWSGlueServiceRole + AmazonS3FullAccess durante testes; em produção restrinja ao mínimo necessário.

Bash (criação do Glue Job via CLI)

aws glue create-job \

--name silver-transform \

--role <GLUE_IAM_ROLE> \

--command '{"Name":"glueetl","ScriptLocation":"s3://br-medalhao-bronze/scripts/silver_transform.py"}'

Importante: Faço o upload do script silver_transform.py para s3://br-medalhao-bronze/scripts/ antes de criar o job.

Console

Vá em AWS Glue → ETL Jobs

Name: silver-transform. IAM role: escolha a role com S3/Glue.

Escolha Spark (Glue ETL).

Script: cole ou aponte para s3://br-medalhao-bronze/scripts/silver_transform.py

- Input: br-medalhao-bronze

- Output: br-medalhao-silver.

Resumidamente: O que o script deve fazer

Ler CSV INMET do Bronze; parsear coluna de data (DATA) para data (DateType).

Calcular ano = year(data) e semana = weekofyear(data) (colunas inteiras).

Ler CSV ANP do Bronze; garantir preco_medio como float e que exista ano e semana (se ANP trouxer ano/semana já, usar; caso contrário derivar de colunas de data/mês).

Gravar Parquet em:

s3://br-medalhao-silver/inmet/

s3://br-medalhao-silver/anp/

2. 4 — Camada Gold: Criar tabela analítica unificada.

Objetivo: tabela analítica semanal integrando clima (INMET) e preço (ANP).

Athena (Bash)

aws athena start-query-execution \

--query-string "CREATE TABLE gold_mobilidade AS

SELECT s.linha, s.horario, i.temp_max, a.preco_medio

FROM silver_sptrans s

LEFT JOIN silver_inmet i ON date(s.horario)=i.data

LEFT JOIN silver_anp a ON weekofyear(s.horario)=a.semana;" \

--result-configuration OutputLocation=s3://br-medalhao-gold/queries/

Console

Vá em Athena → Editor.

Selecione br_medalhao_db.

Rode a query acima.

Saída será salva em br-medalhao-gold/queries/.

2.5 — Visualização (QuickSight)

Acesse Amazon QuickSight.

Conecte ao Glue Catalog (tabela gold_mobilidade).

Crie dashboards:

Passageiros transportados vs. temperatura.

Preço médio de combustível vs. mobilidade.

Tendência semanal.

2. 6 — Orquestração (Step Functions)

Pipeline:

Lambda → SPTrans API.

Glue Job → Silver.

Athena → Gold.

QuickSight → Dashboard atualizado.

Pode ser criado tanto via Console (drag and drop) quanto via Bash (JSON de definição do fluxo).