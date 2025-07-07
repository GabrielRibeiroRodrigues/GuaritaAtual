#!/usr/bin/env python3
"""
Script para gerar imagem de teste para o leitor de placas.
Cria uma imagem simples com texto simulando uma placa brasileira.
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
import os
from datetime import datetime

def criar_imagem_placa(texto_placa="ABC1234", nome_arquivo=None):
    """
    Cria uma imagem simples simulando uma placa brasileira.
    
    Args:
        texto_placa (str): Texto da placa a ser gerado
        nome_arquivo (str): Nome do arquivo de saída (opcional)
    """
    # Dimensões da imagem (proporção similar a uma placa real)
    width = 400
    height = 130
    
    # Criar imagem branca
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    # Adicionar borda preta (simular placa)
    cv2.rectangle(img, (10, 10), (width-10, height-10), (0, 0, 0), 3)
    
    # Configurações do texto
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 2.5
    color = (0, 0, 0)  # Preto
    thickness = 4
    
    # Calcular posição central do texto
    text_size = cv2.getTextSize(texto_placa, font, font_scale, thickness)[0]
    text_x = (width - text_size[0]) // 2
    text_y = (height + text_size[1]) // 2
    
    # Adicionar texto da placa
    cv2.putText(img, texto_placa, (text_x, text_y), font, font_scale, color, thickness)
    
    # Adicionar detalhes extras para parecer mais realista
    # Linha superior (simular "BRASIL")
    cv2.putText(img, "BRASIL", (width//2 - 40, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)
    
    # Retângulo azul pequeno (simular bandeira)
    cv2.rectangle(img, (20, 15), (50, 40), (255, 0, 0), -1)
    
    return img

def main():
    """Função principal para criar imagens de teste."""
    
    # Definir caminhos
    pasta_base = os.path.join(os.path.expanduser("~"), "placas_detectadas")
    pasta_teste = os.path.join(pasta_base, "teste")
    data_hoje = datetime.now().strftime("%Y-%m-%d")
    pasta_teste_data = os.path.join(pasta_teste, data_hoje)
    
    # Criar diretórios se não existirem
    os.makedirs(pasta_teste_data, exist_ok=True)
    
    print("🧪 GERADOR DE IMAGENS DE TESTE")
    print("============================")
    print(f"📁 Pasta de destino: {pasta_teste_data}")
    
    # Lista de placas de teste
    placas_teste = [
        ("ABC1234", "placa_001_123_456.jpg"),
        ("DEF5678", "placa_002_124_789.jpg"),
        ("GHI9012", "placa_003_125_321.jpg"),
        ("JKL3456", "teste_placa_004.jpg"),
        ("MNO7890", "exemplo_placa_005.jpg"),
    ]
    
    images_created = 0
    
    for texto_placa, nome_arquivo in placas_teste:
        caminho_completo = os.path.join(pasta_teste_data, nome_arquivo)
        
        # Verificar se já existe
        if os.path.exists(caminho_completo):
            print(f"⏭️ Pulando {nome_arquivo} (já existe)")
            continue
        
        try:
            # Criar imagem
            img = criar_imagem_placa(texto_placa)
            
            # Salvar
            cv2.imwrite(caminho_completo, img)
            print(f"✅ Criada: {nome_arquivo} (placa: {texto_placa})")
            images_created += 1
            
        except Exception as e:
            print(f"❌ Erro ao criar {nome_arquivo}: {e}")
    
    # Criar uma imagem com qualidade reduzida para testar detecção com baixa confiança
    try:
        # Imagem pequena e borrada
        img_low_quality = criar_imagem_placa("XYZ9999")
        img_low_quality = cv2.resize(img_low_quality, (200, 65))  # Reduzir tamanho
        img_low_quality = cv2.GaussianBlur(img_low_quality, (3, 3), 0)  # Adicionar blur
        
        caminho_low_quality = os.path.join(pasta_teste_data, "placa_baixa_qualidade_999.jpg")
        if not os.path.exists(caminho_low_quality):
            cv2.imwrite(caminho_low_quality, img_low_quality)
            print(f"✅ Criada: placa_baixa_qualidade_999.jpg (teste de baixa confiança)")
            images_created += 1
    except Exception as e:
        print(f"⚠️ Não foi possível criar imagem de baixa qualidade: {e}")
    
    print(f"\n🎉 Concluído! {images_created} imagens criadas.")
    print(f"📁 Local: {pasta_teste_data}")
    print("\n🚀 Para testar, execute:")
    print("   python3 leitor_placas_debian.py")
    
    # Listar arquivos criados
    print(f"\n📋 Arquivos na pasta de teste:")
    try:
        for arquivo in sorted(os.listdir(pasta_teste_data)):
            if arquivo.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                caminho = os.path.join(pasta_teste_data, arquivo)
                tamanho = os.path.getsize(caminho)
                print(f"   📄 {arquivo} ({tamanho} bytes)")
    except Exception as e:
        print(f"   ❌ Erro ao listar arquivos: {e}")

if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("❌ Erro: OpenCV não está instalado.")
        print("💡 Instale com: pip3 install opencv-python")
        print(f"Detalhes: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")
        print("💡 Verifique se você tem permissões para criar arquivos na pasta home.")
