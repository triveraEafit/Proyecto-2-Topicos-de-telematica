#!/bin/bash
# Correr este script en la instancia EC2
# Uso: bash deploy.sh <S3_BUCKET> [AWS_REGION]

S3_BUCKET=$1
AWS_REGION=${2:-us-east-1}

if [ -z "$S3_BUCKET" ]; then
  echo "ERROR: debes pasar el bucket como argumento. Ej: bash deploy.sh mi-bucket"
  exit 1
fi

echo "Instalando dependencias..."
pip install -r requirements.txt

echo "Iniciando Streamlit en background..."
export S3_BUCKET=$S3_BUCKET
export AWS_REGION=$AWS_REGION

nohup streamlit run app.py \
  --server.port=8501 \
  --server.address=0.0.0.0 \
  > streamlit.log 2>&1 &

echo "Streamlit corriendo en puerto 8501"
echo "IP publica: $(curl -s ifconfig.me)"
echo "Configura API Gateway apuntando a: http://$(curl -s ifconfig.me):8501"
