#!/bin/bash

# Script para configurar ambiente de teste do leitor de placas Debian
# Execute com: chmod +x setup_teste_debian.sh && ./setup_teste_debian.sh

echo "🧪 CONFIGURADOR DE TESTE - LEITOR DE PLACAS DEBIAN"
echo "================================================="

# Definir variáveis
PASTA_BASE="$HOME/placas_detectadas"
PASTA_TESTE="$PASTA_BASE/teste"
DATA_HOJE=$(date +"%Y-%m-%d")
PASTA_TESTE_DATA="$PASTA_TESTE/$DATA_HOJE"

echo "📁 Criando estrutura de pastas..."

# Criar estrutura de diretórios
mkdir -p "$PASTA_TESTE_DATA"
chmod 755 "$PASTA_TESTE"
chmod 755 "$PASTA_TESTE_DATA"

echo "✅ Pasta teste criada: $PASTA_TESTE_DATA"

# Criar imagem de teste simples com texto simulando placa
echo "🖼️ Criando imagem de teste..."

# Verifica se ImageMagick está instalado
if command -v convert &> /dev/null; then
    # Cria uma imagem de teste com texto simulando uma placa brasileira
    convert -size 300x100 xc:white \
            -font Arial -pointsize 24 -fill black \
            -gravity center -annotate 0 "ABC1234" \
            "$PASTA_TESTE_DATA/placa_001_123_456.jpg"
    
    echo "✅ Imagem de teste criada: placa_001_123_456.jpg"
    echo "   Placa simulada: ABC1234"
    
elif command -v python3 &> /dev/null; then
    # Alternativa usando Python se ImageMagick não estiver disponível
    python3 -c "
import cv2
import numpy as np

# Criar imagem branca
img = np.ones((100, 300, 3), dtype=np.uint8) * 255

# Adicionar texto simulando placa
cv2.putText(img, 'ABC1234', (50, 60), cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 3)

# Salvar imagem
cv2.imwrite('$PASTA_TESTE_DATA/placa_001_123_456.jpg', img)
print('Imagem de teste criada com Python')
"
    echo "✅ Imagem de teste criada com Python"
    
else
    echo "⚠️ ImageMagick ou Python não encontrados."
    echo "   Você pode criar manualmente uma imagem de placa em:"
    echo "   $PASTA_TESTE_DATA/"
    echo "   Formato recomendado: placa_FRAME_ID_CARID.jpg"
fi

# Criar arquivo de exemplo adicional se o usuário quiser copiar imagens reais
echo "📝 Criando guia de uso..."

cat > "$PASTA_TESTE/COMO_USAR.txt" << EOF
🧪 GUIA DE TESTE - LEITOR DE PLACAS DEBIAN
=========================================

PASTA DE TESTE: $PASTA_TESTE

1️⃣ ADICIONAR IMAGENS DE TESTE:
   - Copie imagens de placas para: $PASTA_TESTE_DATA/
   - Formato de nome: placa_FRAME_ID_CARID.jpg
   - Exemplo: placa_001_123_456.jpg

2️⃣ EXECUTAR TESTE:
   cd $(dirname "$0")
   python3 leitor_placas_debian.py

3️⃣ COMPORTAMENTO ESPERADO:
   ✅ Detecção automática do modo teste
   ✅ Processamento das imagens
   ✅ Exibição de resultados detalhados
   ✅ Preservação das imagens (não são deletadas)

4️⃣ EXEMPLOS DE NOMES DE ARQUIVO:
   - placa_001_123_456.jpg  (Frame 1, Car ID 456)
   - placa_002_124_789.jpg  (Frame 2, Car ID 789)
   - teste_placa_001.jpg    (Formato simplificado)

5️⃣ FORMATOS SUPORTADOS:
   - JPG, JPEG, PNG, BMP

6️⃣ MONITORAMENTO CONTÍNUO:
   - Depois do teste inicial, o sistema continua monitorando
   - Novas imagens adicionadas serão processadas automaticamente

7️⃣ LOGS DE TESTE:
   - Procure por linhas com [TESTE] no output
   - Resultados detalhados são exibidos no terminal

Criado em: $(date)
EOF

echo "✅ Guia criado: $PASTA_TESTE/COMO_USAR.txt"

# Verificar se existe uma imagem de teste
if ls "$PASTA_TESTE_DATA"/*.{jpg,jpeg,png,bmp} 1> /dev/null 2>&1; then
    echo ""
    echo "🎉 CONFIGURAÇÃO CONCLUÍDA!"
    echo "========================"
    echo "📁 Pasta teste: $PASTA_TESTE_DATA"
    echo "🖼️ Imagens encontradas:"
    ls -la "$PASTA_TESTE_DATA"/*.{jpg,jpeg,png,bmp} 2>/dev/null || echo "   (nenhuma imagem encontrada)"
    echo ""
    echo "🚀 COMO EXECUTAR O TESTE:"
    echo "   cd $(dirname "$0")"
    echo "   python3 leitor_placas_debian.py"
    echo ""
    echo "📋 O QUE ESPERAR:"
    echo "   - Detecção automática do modo teste"
    echo "   - Processamento das imagens de teste"
    echo "   - Logs detalhados com emoji 🧪"
    echo "   - Imagens preservadas para testes futuros"
else
    echo ""
    echo "⚠️ ATENÇÃO!"
    echo "=========="
    echo "Nenhuma imagem de teste foi criada automaticamente."
    echo "Por favor, adicione manualmente imagens de placas em:"
    echo "$PASTA_TESTE_DATA/"
    echo ""
    echo "Formato recomendado de nome: placa_001_123_456.jpg"
fi

echo ""
echo "📖 Para mais informações, leia: $PASTA_TESTE/COMO_USAR.txt"
echo "🐞 Em caso de problemas, verifique as permissões das pastas"
