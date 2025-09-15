import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql.functions import col, to_date

# Recebe o nome do Job
args = getResolvedOptions(sys.argv, ['JOB_NAME'])
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# -----------------------------
# 1️⃣ Ler datasets do Bronze
# -----------------------------
bronze_bucket = "s3://br-medalhao-bronze/"

# INMET (ler todos os arquivos da pasta 2022)
df_inmet = (
    spark.read
         .option("header", True)
         .option("inferSchema", True)
         .option("delimiter", ";")   # necessário para CSVs do INMET
         .csv(f"{bronze_bucket}inmet/2022/")  # lê todos os arquivos dentro da pasta
)

# Mostrar colunas para debug (aparece nos logs do Glue)
print("Colunas INMET:", df_inmet.columns)

# Renomear coluna de DATA -> data (se existir)
if "DATA" in df_inmet.columns:
    df_inmet = df_inmet.withColumnRenamed("DATA", "data")
elif "Data" in df_inmet.columns:
    df_inmet = df_inmet.withColumnRenamed("Data", "data")

# Tratar campo de data
if "data" in df_inmet.columns:
    df_inmet = df_inmet.withColumn("data", to_date(col("data"), "yyyy-MM-dd"))

# Renomear temperatura máxima se existir
if "TEMPERATURA_MAX" in df_inmet.columns:
    df_inmet = df_inmet.withColumnRenamed("TEMPERATURA_MAX", "temp_max")
elif "MaxTemp" in df_inmet.columns:
    df_inmet = df_inmet.withColumnRenamed("MaxTemp", "temp_max")

# ANP (um CSV só, separado por ;)
df_anp = (
    spark.read
         .option("header", True)
         .option("inferSchema", True)
         .option("delimiter", ";")
         .csv(f"{bronze_bucket}anp/")  # lê todos os arquivos da pasta
)

print("Colunas ANP:", df_anp.columns)

# Padronizar colunas principais da ANP
if "PREÇO MÉDIO REVENDA" in df_anp.columns:
    df_anp = df_anp.withColumnRenamed("PREÇO MÉDIO REVENDA", "preco_medio")
if "MÊS" in df_anp.columns:
    df_anp = df_anp.withColumnRenamed("MÊS", "mes")
if "SEMANA" in df_anp.columns:
    df_anp = df_anp.withColumnRenamed("SEMANA", "semana")

# Converter preço para float
if "preco_medio" in df_anp.columns:
    df_anp = df_anp.withColumn("preco_medio", col("preco_medio").cast("float"))

# -----------------------------
# 2️⃣ Salvar datasets no Silver
# -----------------------------
silver_bucket = "s3://br-medalhao-silver/"

df_inmet.write.mode("overwrite").parquet(f"{silver_bucket}inmet/2022/")
df_anp.write.mode("overwrite").parquet(f"{silver_bucket}anp/")

job.commit()
