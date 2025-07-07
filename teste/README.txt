PASTA DE TESTE - LEITOR DE PLACAS DEBIAN
===========================================

Esta pasta é usada para testar o funcionamento do leitor de placas.

ESTRUTURA SIMPLES:
- teste/
  ├── README.txt (este arquivo)
  └── [imagens de placas para teste]

COMO USAR:
1. Coloque imagens de placas diretamente nesta pasta
2. Execute o leitor_placas_debian.py
3. As imagens serão processadas e DELETADAS automaticamente

FORMATO SUGERIDO PARA NOMES DE ARQUIVO:
- placa_FRAME_ID_CARID.jpg
- Exemplo: placa_001_123_456.jpg
- Mas qualquer nome funcionará para teste

NOTAS:
- As imagens SERÃO REMOVIDAS após processamento
- Logs aparecerão no terminal com resultados detalhados
- Para preservar imagens, faça backup antes de colocar na pasta
- O salvamento no banco de dados está DESABILITADO em modo teste

EXEMPLO DE USO:
1. Copie uma imagem de placa para esta pasta:
   cp minha_placa.jpg teste/placa_001_123_456.jpg

2. Execute o leitor:
   python3 leitor_placas_debian.py

3. Observe os logs de processamento no terminal

4. A imagem será removida automaticamente após o processamento

Criado em: 2025-07-07
