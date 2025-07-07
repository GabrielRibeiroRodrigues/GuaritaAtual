#!/usr/bin/env python3
"""
Script para gerar imagens de teste para o leitor de placas.
Cria imagens simples com texto simulando placas brasileiras.
Versão atualizada para estrutura simples de teste.
"""

import cv2
import numpy as np
import os

def criar_imagem_teste_placa(texto_placa="ABC1234", nome_arquivo="placa_001_123_456.jpg"):
    """
    Cria uma imagem de teste simulando uma placa brasileira.
    
    Args:
        texto_placa (str): Texto da placa (formato brasileiro)
        nome_arquivo (str): Nome do arquivo a ser salvo
    """
    # Dimensões da imagem (proporção de placa brasileira)
    largura, altura = 400, 130
    
    # Cria imagem branca
    img = np.ones((altura, largura, 3), dtype=np.uint8) * 255
    
    # Adiciona borda preta
    cv2.rectangle(img, (5, 5), (largura-5, altura-5), (0, 0, 0), 2)
    
    # Configura fonte
    fonte = cv2.FONT_HERSHEY_SIMPLEX
    escala_fonte = 1.8
    espessura = 3
    cor_texto = (0, 0, 0)  # Preto
    
    # Calcula posição do texto para centralizar
    (largura_texto, altura_texto), baseline = cv2.getTextSize(texto_placa, fonte, escala_fonte, espessura)
    x = (largura - largura_texto) // 2
    y = (altura + altura_texto) // 2
    
    # Adiciona o texto da placa
    cv2.putText(img, texto_placa, (x, y), fonte, escala_fonte, cor_texto, espessura)
    
    # Adiciona pequenas marcações para simular parafusos
    cv2.circle(img, (30, 30), 3, (128, 128, 128), -1)
    cv2.circle(img, (largura-30, 30), 3, (128, 128, 128), -1)
    cv2.circle(img, (30, altura-30), 3, (128, 128, 128), -1)
    cv2.circle(img, (largura-30, altura-30), 3, (128, 128, 128), -1)
    
    # Salva a imagem na pasta teste (estrutura simples)
    pasta_teste = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teste")
    caminho_completo = os.path.join(pasta_teste, nome_arquivo)
    
    cv2.imwrite(caminho_completo, img)
    print(f"✅ Imagem de teste criada: {caminho_completo}")
    print(f"📝 Texto da placa: {texto_placa}")
    print(f"📏 Dimensões: {largura}x{altura}")
    
    return caminho_completo

def main():
    """Função principal para criar imagens de teste"""
    print("🧪 GERADOR DE IMAGENS DE TESTE PARA LEITOR DE PLACAS")
    print("=" * 55)
    
    # Verifica se a pasta teste existe
    pasta_teste = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teste")
    if not os.path.exists(pasta_teste):
        print(f"❌ Pasta teste não encontrada: {pasta_teste}")
        print("Execute primeiro o leitor_placas_debian.py para criar a estrutura.")
        return
    
    # Cria algumas imagens de teste
    exemplos = [
        ("ABC1234", "placa_001_123_456.jpg"),  # Formato antigo
        ("BRA2E19", "placa_002_124_789.jpg"),  # Formato Mercosul
        ("XYZ9876", "placa_003_125_101.jpg"),  # Formato antigo
        ("CTB4A56", "placa_004_126_112.jpg"),  # Formato Mercosul
    ]
    
    print(f"📁 Criando imagens de teste em: {pasta_teste}")
    print()
    
    for texto, nome in exemplos:
        try:
            criar_imagem_teste_placa(texto, nome)
        except Exception as e:
            print(f"❌ Erro ao criar {nome}: {e}")
    
    print()
    print("🎯 PRÓXIMOS PASSOS:")
    print("1. Execute: python3 leitor_placas_debian.py")
    print("2. Observe os logs de processamento")
    print("3. As imagens serão automaticamente removidas após processamento")
    print()
    print("💡 DICA: Para testar com suas próprias imagens,")
    print(f"   copie-as para a pasta: {pasta_teste}")

if __name__ == "__main__":
    main()
