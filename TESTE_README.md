# 🧪 TESTE DO LEITOR DE PLACAS DEBIAN

Este documento explica como testar o sistema de leitura de placas na versão Debian/Linux.

## 📋 Pré-requisitos

```bash
# Dependências do sistema
sudo apt update
sudo apt install python3-opencv python3-pip

# Dependências Python (PostgreSQL temporariamente desabilitado)
pip3 install paddleocr paddlepaddle opencv-python numpy Pillow
```

## 🚀 Configuração Rápida

### Método Manual
```bash
# Colocar imagens na pasta teste na raiz do projeto
# Exemplo: ./teste/imagem_placa.jpg
```

## 📁 Estrutura de Pastas

```
./GuaritaAtual/
├── teste/                    # Pasta de teste simples
│   ├── README.txt
│   ├── imagem_placa.jpg      # Suas imagens de teste
│   └── placa_001_123_456.webp
├── leitor_placas_debian.py   # Script principal
└── util_debian.py           # Módulo com OCR
```

## 🎯 Como Executar

```bash
# Executar o leitor de placas
python3 leitor_placas_debian.py
```

## 🔍 O Que Esperar (MODO TESTE - Sem PostgreSQL)

### 1. Detecção Automática do Modo Teste
```
[TESTE] Imagem encontrada para teste: imagem_placa.webp
🧪 [TESTE] Modo teste detectado! Processando imagens de teste...
```

### 2. Processamento Detalhado
```
[TESTE] Processando imagem de teste: imagem_placa.webp
[TESTE] Imagem carregada via PIL (formato WEBP)
[TESTE] ✅ PLACA DETECTADA: ABC1234
[TESTE] 📊 Confiança: 0.95
[TESTE] 🎯 Frame: 999, Car ID: 888
[TESTE] ✅ Confiança acima do mínimo (0.1)

🚗 [PLACA_DETECTADA] Frame: 999, Car ID: 888
📋 [PLACA_DETECTADA] Placa: ABC1234
📊 [PLACA_DETECTADA] Confiança: 0.95
🕒 [PLACA_DETECTADA] Data/Hora: 2025-07-08 10:30:15
------------------------------------------------------------

[TESTE] 🗑️ Arquivo de teste removido: imagem_placa.webp
```

### 3. Resumo Final
```
🧪 [TESTE] Concluído! 1 arquivos processados.
🧪 [TESTE] Para teste contínuo, o monitoramento normal continuará...
```

## 📝 Formatos de Nome de Arquivo

### Formato Recomendado
- `placa_FRAME_ID_CARID.jpg`
- Exemplo: `placa_001_123_456.jpg`
  - Frame: 1
  - Car ID: 456

### Formatos Alternativos Aceitos
- `teste_placa_001.jpg`
- `qualquer_nome_123_789.webp`
- `imagem_placa.png` (usará Frame: 999, Car ID: 888)

## 🎨 Tipos de Arquivo Suportados
- JPG / JPEG
- PNG
- BMP
- WEBP ✨ (requer Pillow)
- TIFF / TIF

### 📝 Nota sobre WebP
Arquivos WebP são suportados automaticamente através da biblioteca Pillow. Se você receber erros sobre WebP, instale:
```bash
pip3 install Pillow
```

## ⚙️ Diferenças do Modo Teste (Sem PostgreSQL)

| Aspecto | Modo Normal | Modo Teste |
|---------|-------------|------------|
| **Detecção** | Automática se há arquivos em `./teste/` | Manual |
| **Salvamento DB** | ❌ Exibe no terminal apenas | ❌ Exibe no terminal apenas |
| **Remoção Arquivo** | ✅ Remove após processar | ✅ Remove após processar |
| **Logs** | Padrão | 🧪 Detalhados com emoji |
| **Timeout** | 2 segundos | 0.5 segundos |
| **Parse Nome** | Rigoroso | Flexível |

## 🐞 Solução de Problemas

### Problema: Sistema não detecta imagens na pasta teste
```bash
# 1. Verificar se as imagens estão no local correto
ls -la ./teste/

# 2. Verificar formatos suportados
# Aceitos: .jpg, .jpeg, .png, .bmp, .webp, .tiff, .tif
# Se sua imagem é .webp, certifique-se que o Pillow está instalado

# 3. Instalar Pillow se necessário
pip3 install Pillow

# 4. Verificar se há logs de detecção
python3 leitor_placas_debian.py
# Deve mostrar: "[TESTE] Imagem encontrada para teste: nome_arquivo.webp"
```

### Problema: Erro ao carregar WebP
```bash
# Instalar Pillow
pip3 install Pillow

# Verificar instalação
python3 -c "from PIL import Image; print('Pillow OK:', Image.__version__)"
```

### Problema: Dependências
```bash
# Verificar instalação do OpenCV
python3 -c "import cv2; print('OpenCV OK:', cv2.__version__)"

# Verificar PaddleOCR
python3 -c "from paddleocr import PaddleOCR; print('PaddleOCR OK')"
```

## 📊 Interpretando Resultados

### Confiança Alta (≥ 0.8)
```
[TESTE] ✅ PLACA DETECTADA: ABC1234
[TESTE] 📊 Confiança: 0.95
🚗 [PLACA_DETECTADA] Frame: 999, Car ID: 888
📋 [PLACA_DETECTADA] Placa: ABC1234
```
- Resultado muito confiável
- Placa claramente legível

### Confiança Baixa (< 0.1)
```
[TESTE] ⚠️ Confiança abaixo do mínimo (0.1)
[TESTE] ❌ Placa não será salva: ABC1234 (confiança: 0.05)
```
- Resultado duvidoso
- Verificar qualidade da imagem

### Sem Detecção
```
[TESTE] ❌ Nenhuma placa detectada em: imagem.jpg
```
- Nenhum texto reconhecido
- Verificar se há uma placa visível na imagem

## 🔧 Configurações Avançadas

### Alterar Confiança Mínima
Edite no arquivo `leitor_placas_debian.py`:
```python
confianca_gravar_texto = 0.1  # Valor entre 0.0 e 1.0
```

### Habilitar PostgreSQL Novamente
Para reabilitar o banco de dados PostgreSQL:
1. Descomente as linhas no `util_debian.py`
2. Instale psycopg2: `pip3 install psycopg2-binary`
3. Configure as variáveis de ambiente do banco

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs no terminal
2. Confirme que as dependências estão instaladas (sem PostgreSQL)
3. Teste com uma imagem simples primeiro
4. Verifique se o arquivo está na pasta `./teste/`

---

**Última atualização:** $(date)
**Versão:** Debian/Linux v1.0 (Modo Teste - PostgreSQL Desabilitado)
**Status:** ✅ Pronto para testes simples com exibição no terminal
