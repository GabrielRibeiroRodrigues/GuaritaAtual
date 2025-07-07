# 🧪 ESTRUTURA DE TESTE PARA LEITOR DE PLACAS DEBIAN

## 📁 Estrutura Criada

```
projeto/
├── leitor_placas_debian.py     # Script principal adaptado para Debian
├── util_debian.py              # Módulo de utilidades para Debian
├── criar_imagens_teste.py      # Gerador de imagens de teste
└── teste/                      # Pasta de teste (estrutura simples)
    ├── README.txt              # Instruções de uso
    └── [suas imagens aqui]     # Imagens para teste
```

## 🚀 Como Usar

### 1. **Preparar o Ambiente**
```bash
# Instalar dependências
sudo apt update
sudo apt install python3-opencv python3-pip
pip3 install psycopg2-binary paddleocr paddlepaddle

# Configurar banco de dados (opcional para teste)
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=guarita
export DB_USER=postgres
export DB_PASSWORD=sua_senha
```

### 2. **Gerar Imagens de Teste (Opcional)**
```bash
# Criar imagens de exemplo
python3 criar_imagens_teste.py
```

### 3. **Adicionar Suas Próprias Imagens**
```bash
# Copiar imagem real para teste
cp minha_placa.jpg teste/placa_real_001.jpg

# Ou várias imagens
cp *.jpg teste/
```

### 4. **Executar o Teste**
```bash
# Rodar o leitor
python3 leitor_placas_debian.py
```

## 🎯 **Comportamento do Sistema**

### **Detecção Automática de Modo Teste**
- ✅ Detecta automaticamente se há imagens na pasta `teste/`
- 🧪 Exibe logs detalhados para teste
- 🗑️ **Remove imagens após processamento** (conforme solicitado)
- 💾 Banco de dados **DESABILITADO** em modo teste

### **Logs de Teste Detalhados**
```
🧪 [TESTE] Modo teste detectado! Processando imagens de teste...
[TESTE] Processando imagem de teste: placa_001_123_456.jpg
[TESTE] Imagem carregada: (130, 400)
[TESTE] ✅ PLACA DETECTADA: ABC1234
[TESTE] 📊 Confiança: 0.95
[TESTE] 🎯 Frame: 1, Car ID: 456
[TESTE] ✅ Confiança acima do mínimo (0.1)
[TESTE] 💾 Salvamento no banco DESABILITADO (modo teste)
[TESTE] 🗑️ Arquivo de teste removido: placa_001_123_456.jpg
```

### **Processamento Normal**
- 📁 Monitora pasta `~/placas_detectadas/` para operação normal
- 🗑️ Remove imagens após processamento
- 💾 Salva resultados no banco de dados
- 🔄 Reconexão automática do banco

## ⚙️ **Configurações Especiais**

### **Pasta de Teste**
- 📍 **Localização**: `./teste/` (raiz do projeto)
- 🏗️ **Estrutura**: Simples (sem subpastas)
- 🗑️ **Comportamento**: Deleta imagens após processamento
- 💾 **Banco**: Desabilitado para teste

### **Arquivo README na Pasta Teste**
- 📋 Instruções detalhadas dentro da pasta
- 🔄 Atualizado automaticamente
- 📝 Exemplos de uso

## 🛠️ **Comandos Úteis**

```bash
# Verificar se há imagens na pasta teste
ls -la teste/*.jpg

# Executar apenas uma vez (Ctrl+C após o teste)
python3 leitor_placas_debian.py

# Monitorar logs em tempo real
python3 leitor_placas_debian.py | tee teste_logs.txt

# Limpar pasta teste
rm teste/*.jpg teste/*.png

# Recriar imagens de exemplo
python3 criar_imagens_teste.py
```

## 🎭 **Cenários de Teste**

### **Teste Básico**
1. Execute `python3 criar_imagens_teste.py`
2. Execute `python3 leitor_placas_debian.py`
3. Observe os logs de processamento

### **Teste com Suas Imagens**
1. Copie suas imagens para `teste/`
2. Execute `python3 leitor_placas_debian.py`
3. Observe se as placas são detectadas corretamente

### **Teste de Performance**
1. Adicione muitas imagens em `teste/`
2. Execute e meça tempo de processamento
3. Verifique uso de memória

## 📊 **Interpretação dos Resultados**

### **Sucesso ✅**
```
[TESTE] ✅ PLACA DETECTADA: ABC1234
[TESTE] 📊 Confiança: 0.95
```

### **Baixa Confiança ⚠️**
```
[TESTE] ⚠️ Confiança abaixo do mínimo (0.1)
```

### **Falha na Detecção ❌**
```
[TESTE] ❌ Nenhuma placa detectada em: imagem.jpg
```

### **Problema na Imagem 🔧**
```
[TESTE] Erro: Não foi possível ler a imagem: corrupted.jpg
```

## 🔍 **Troubleshooting**

### **Pasta teste não criada**
- Execute `leitor_placas_debian.py` primeiro
- Verifique permissões do diretório

### **Imagens não processadas**
- Verifique formato (jpg, png, bmp)
- Confirme que não são arquivos ocultos (.)
- Verifique permissões de leitura

### **OCR não funciona**
- Instale: `pip3 install paddleocr paddlepaddle`
- Verifique: `python3 -c "import paddleocr; print('OK')"`

---

**Criado especificamente para ambiente Debian/Linux** 🐧  
**Estrutura simples conforme solicitado** ✨  
**Deleção automática das imagens** 🗑️
