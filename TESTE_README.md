# 🧪 TESTE DO LEITOR DE PLACAS DEBIAN

Este documento explica como testar o sistema de leitura de placas na versão Debian/Linux.

## 📋 Pré-requisitos

```bash
# Dependências do sistema
sudo apt update
sudo apt install python3-opencv python3-pip

# Dependências Python
pip3 install psycopg2-binary paddleocr paddlepaddle opencv-python numpy
```

## 🚀 Configuração Rápida

### Método 1: Script Automático
```bash
chmod +x setup_teste_debian.sh
./setup_teste_debian.sh
```

### Método 2: Manual
```bash
# Criar estrutura de pastas
mkdir -p ~/placas_detectadas/teste/$(date +%Y-%m-%d)

# Copiar imagens de placas para teste
cp suas_imagens_de_placas.jpg ~/placas_detectadas/teste/$(date +%Y-%m-%d)/
```

## 📁 Estrutura de Pastas

```
~/placas_detectadas/
├── teste/
│   ├── README.txt
│   ├── COMO_USAR.txt
│   └── 2025-07-07/          # Data atual
│       ├── placa_001_123_456.jpg
│       ├── placa_002_124_789.jpg
│       └── teste_placa_003.jpg
└── 2025-07-07/              # Pasta de produção
    └── (imagens reais do sistema)
```

## 🎯 Como Executar

```bash
# Executar o leitor de placas
python3 leitor_placas_debian.py
```

## 🔍 O Que Esperar

### 1. Detecção Automática do Modo Teste
```
🧪 [TESTE] Modo teste detectado! Processando imagens de teste...
```

### 2. Processamento Detalhado
```
[TESTE] Processando imagem de teste: placa_001_123_456.jpg
[TESTE] Imagem carregada: (100, 300)
[TESTE] ✅ PLACA DETECTADA: ABC1234
[TESTE] 📊 Confiança: 0.95
[TESTE] 🎯 Frame: 1, Car ID: 456
[TESTE] ✅ Confiança acima do mínimo (0.1)
[TESTE] 💾 Salvamento no banco DESABILITADO (modo teste)
[TESTE] 📁 Arquivo preservado para testes futuros: placa_001_123_456.jpg
```

### 3. Resumo Final
```
🧪 [TESTE] Concluído! 3 arquivos processados.
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
- `qualquer_nome_123_789.jpg`
- `imagem_placa.jpg` (usará valores padrão)

## 🎨 Tipos de Arquivo Suportados
- JPG / JPEG
- PNG
- BMP

## ⚙️ Diferenças do Modo Teste

| Aspecto | Modo Normal | Modo Teste |
|---------|-------------|------------|
| **Detecção** | Automática se há arquivos em `~/placas_detectadas/teste/` | Manual |
| **Salvamento DB** | ✅ Salva no PostgreSQL | ❌ Não salva (apenas simula) |
| **Remoção Arquivo** | ✅ Remove após processar | ❌ Preserva para testes futuros |
| **Logs** | Padrão | 🧪 Detalhados com emoji |
| **Timeout** | 2 segundos | 0.5 segundos |
| **Parse Nome** | Rigoroso | Flexível |

## 🐞 Solução de Problemas

### Problema: Nenhuma imagem detectada
```bash
# Verificar se as imagens estão no local correto
ls -la ~/placas_detectadas/teste/$(date +%Y-%m-%d)/
```

### Problema: Permissões
```bash
# Corrigir permissões
chmod 755 ~/placas_detectadas/teste/
chmod 644 ~/placas_detectadas/teste/*/*.jpg
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
```
- Resultado muito confiável
- Placa claramente legível

### Confiança Média (0.3 - 0.8)
```
[TESTE] ✅ PLACA DETECTADA: ABC1234
[TESTE] 📊 Confiança: 0.65
```
- Resultado aceitável
- Pode precisar de validação manual

### Confiança Baixa (< 0.3)
```
[TESTE] ⚠️ Confiança abaixo do mínimo (0.1)
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

### Habilitar Salvamento no Banco (Modo Teste)
Remova o comentário da linha de salvamento em `processar_imagem_teste()`:
```python
# salvar_no_postgres(frame_nmr, car_id, texto_detectado, confianca_texto_detectado)
```

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs no terminal
2. Confirme que as dependências estão instaladas
3. Teste com uma imagem simples primeiro
4. Verifique permissões de arquivo e pasta

---

**Última atualização:** $(date)
**Versão:** Debian/Linux v1.0
