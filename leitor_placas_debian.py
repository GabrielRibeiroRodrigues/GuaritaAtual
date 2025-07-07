import os
import cv2
import time
import gc
import signal  # Import for signal handling
from datetime import datetime, timedelta
from util_debian import (
    ler_placas2,
    salvar_no_postgres,
    flush_buffer_leituras,
    close_db_connection,
)  # Import new functions from Debian-specific module

# Caminho para ambiente Linux/Debian - usando diretório home do usuário
pasta_base = os.path.join(os.path.expanduser("~"), "placas_detectadas")
# Pasta de teste simples na raiz do projeto
pasta_teste = os.path.join(os.path.dirname(os.path.abspath(__file__)), "teste")
confianca_gravar_texto = 0.1  # Mantido, mas a lógica de correção pode ajudar placas com menor confiança inicial


def remover_arquivo_com_retry(caminho_arquivo, max_tentativas=3, delay=0.1):
    """
    Remove um arquivo com múltiplas tentativas para lidar com locks temporários.
    Adaptado para ambiente Linux/Debian.
    """
    for tentativa in range(max_tentativas):
        try:
            if os.path.exists(caminho_arquivo):
                # No Linux, remove diretamente
                os.remove(caminho_arquivo)
                print(f"[INFO] Arquivo removido: {os.path.basename(caminho_arquivo)}")
                return True
            else:
                print(f"[WARN] Arquivo não existe para remoção: {caminho_arquivo}")
                return True  # Considera sucesso se não existe
        except PermissionError:
            print(f"[WARN] Sem permissão para remover arquivo, tentativa {tentativa + 1}/{max_tentativas}: {os.path.basename(caminho_arquivo)}")
            if tentativa < max_tentativas - 1:
                time.sleep(delay * (tentativa + 1))  # Delay crescente
        except OSError as e:
            # No Linux, pode ocorrer OSError quando arquivo está em uso
            print(f"[WARN] Arquivo em uso (OSError), tentativa {tentativa + 1}/{max_tentativas}: {os.path.basename(caminho_arquivo)} - {e}")
            if tentativa < max_tentativas - 1:
                time.sleep(delay * (tentativa + 1))
        except Exception as e:
            print(f"[ERRO] Falha ao remover arquivo {os.path.basename(caminho_arquivo)}: {e}")
            if tentativa < max_tentativas - 1:
                time.sleep(delay)
    
    print(f"[ERRO] Não foi possível remover o arquivo após {max_tentativas} tentativas: {os.path.basename(caminho_arquivo)}")
    return False


def verificar_arquivo_completo(caminho_arquivo, tempo_estabilidade=1):
    """
    Verifica se um arquivo está completo (não está sendo escrito).
    Adaptado para ambiente Linux/Debian com tempo menor de estabilidade.
    """
    try:
        if not os.path.exists(caminho_arquivo):
            return False
        
        # Verifica permissões de leitura
        if not os.access(caminho_arquivo, os.R_OK):
            print(f"[WARN] Sem permissão de leitura para: {os.path.basename(caminho_arquivo)}")
            return False
        
        tamanho_inicial = os.path.getsize(caminho_arquivo)
        time.sleep(tempo_estabilidade)
        
        if not os.path.exists(caminho_arquivo):
            return False
            
        tamanho_final = os.path.getsize(caminho_arquivo)
        
        # Se o tamanho mudou, o arquivo ainda está sendo escrito
        if tamanho_inicial != tamanho_final:
            print(f"[INFO] Arquivo ainda sendo escrito: {os.path.basename(caminho_arquivo)}")
            return False
            
        # Verifica se consegue abrir o arquivo para leitura
        try:
            with open(caminho_arquivo, 'rb') as f:
                # Tenta ler alguns bytes para verificar se não há problemas
                f.read(1)
            return True
        except (PermissionError, IOError, OSError) as e:
            print(f"[INFO] Arquivo com problemas de acesso: {os.path.basename(caminho_arquivo)} - {e}")
            return False
            
    except Exception as e:
        print(f"[WARN] Erro ao verificar arquivo {os.path.basename(caminho_arquivo)}: {e}")
        return False


def processar_imagem(caminho_arquivo):
    nome = os.path.basename(caminho_arquivo)
    arquivo_processado_com_sucesso = False
    img_carregada = False
    
    # Verifica se o arquivo está completo antes de processar
    if not verificar_arquivo_completo(caminho_arquivo):
        print(f"[INFO] Arquivo não está pronto para processamento: {nome}")
        return False
    
    try:
        partes = nome.split("_")
        # Adicionar mais validações para evitar IndexError
        if len(partes) > 3:
            frame_nmr_str = partes[1]
            car_id_str = partes[3]
            frame_nmr = int(frame_nmr_str) if frame_nmr_str.isdigit() else -1
            # Tratar caso onde car_id_str pode não ser um número válido antes de float()
            if "." in car_id_str:
                try:
                    car_id = int(float(car_id_str))
                except ValueError:
                    car_id = -1  # ID inválido se não puder converter
            elif car_id_str.isdigit():
                car_id = int(car_id_str)
            else:
                car_id = -1  # ID inválido
        else:
            frame_nmr = -1
            car_id = -1
    except Exception as e:
        print(f"[WARN] Erro ao parsear nome do arquivo '{nome}': {e}")
        frame_nmr = -1
        car_id = -1

    try:
        # Carregar a imagem
        img = cv2.imread(caminho_arquivo, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[ERRO] Não foi possível ler a imagem: {nome}")
            # Remove arquivo corrompido ou ilegível
            remover_arquivo_com_retry(caminho_arquivo)
            return True  # Retorna True pois o arquivo foi "processado" (removido)

        img_carregada = True
        texto_detectado, confianca_texto_detectado = ler_placas2(img)

        # Libera a imagem da memória explicitamente
        del img

        if (
            texto_detectado is not None
            and confianca_texto_detectado is not None
            and confianca_texto_detectado > confianca_gravar_texto
        ):
            print(
                f"[INFO] Frame: {frame_nmr}, Carro ID: {car_id}, Placa: {texto_detectado}, Confiança: {confianca_texto_detectado:.2f}"
            )
        
        arquivo_processado_com_sucesso = True
        
    except cv2.error as e_cv:
        print(f"[ERRO_CV2] Erro de OpenCV ao processar {nome}: {e_cv}")
        arquivo_processado_com_sucesso = True  # Considera processado mesmo com erro
    except Exception as e_proc:
        print(f"[ERRO_PROC] Erro inesperado ao processar imagem {nome}: {e_proc}")
        arquivo_processado_com_sucesso = True  # Considera processado mesmo com erro
    finally:
        # Remove o arquivo somente se foi carregado com sucesso ou houve erro no processamento
        # Isso garante que arquivos problemáticos não fiquem acumulando
        if img_carregada or arquivo_processado_com_sucesso:
            sucesso_remocao = remover_arquivo_com_retry(caminho_arquivo)
            if not sucesso_remocao:
                print(f"[ERRO] Arquivo não foi removido: {nome}")
        
        gc.collect()  # Coleta de lixo mais frequente pode ajudar em sistemas com pouca memória
    
    return arquivo_processado_com_sucesso


def limpar_arquivos_antigos(pasta_base, idade_maxima_horas=24):
    """
    Remove arquivos órfãos que são muito antigos (provavelmente não processados corretamente).
    Adaptado para ambiente Linux/Debian.
    """
    arquivos_removidos = 0
    tempo_limite = datetime.now() - timedelta(hours=idade_maxima_horas)
    
    try:
        for root, dirs, files in os.walk(pasta_base):
            for arquivo in files:
                caminho_arquivo = os.path.join(root, arquivo)
                try:
                    # Verifica a data de modificação do arquivo
                    timestamp_modificacao = os.path.getmtime(caminho_arquivo)
                    data_modificacao = datetime.fromtimestamp(timestamp_modificacao)
                    
                    if data_modificacao < tempo_limite:
                        print(f"[INFO] Removendo arquivo antigo: {os.path.basename(arquivo)}")
                        if remover_arquivo_com_retry(caminho_arquivo):
                            arquivos_removidos += 1
                            
                except Exception as e:
                    print(f"[WARN] Erro ao verificar arquivo antigo {arquivo}: {e}")
    
    except Exception as e:
        print(f"[ERRO] Erro durante limpeza de arquivos antigos: {e}")
    
    if arquivos_removidos > 0:
        print(f"[INFO] Limpeza concluída: {arquivos_removidos} arquivos antigos removidos")
    
    return arquivos_removidos


def criar_pasta_base():
    """
    Cria a pasta base se não existir, com tratamento de permissões para Linux.
    """
    try:
        if not os.path.exists(pasta_base):
            os.makedirs(pasta_base, mode=0o755)  # Permissões padrão para Linux
            print(f"[INFO] Pasta base criada: {pasta_base}")
        
        # Verifica se tem permissão de escrita
        if not os.access(pasta_base, os.W_OK):
            print(f"[ERRO] Sem permissão de escrita na pasta: {pasta_base}")
            return False
            
        return True
    except Exception as e:
        print(f"[ERRO] Não foi possível criar/acessar a pasta base {pasta_base}: {e}")
        return False


def criar_estrutura_teste():
    """
    Cria uma pasta de teste simples na raiz do projeto.
    Retorna True se a estrutura foi criada/existe, False em caso de erro.
    """
    try:
        # Cria pasta teste simples na raiz do projeto
        if not os.path.exists(pasta_teste):
            os.makedirs(pasta_teste, mode=0o755)
            print(f"[TESTE] Pasta de teste criada: {pasta_teste}")
        
        # Verifica permissões
        if not os.access(pasta_teste, os.W_OK):
            print(f"[ERRO] Sem permissão de escrita na pasta de teste: {pasta_teste}")
            return False
        
        # Cria arquivo README explicativo
        readme_path = os.path.join(pasta_teste, "README.txt")
        if not os.path.exists(readme_path):
            with open(readme_path, 'w') as f:
                f.write(f"""PASTA DE TESTE - LEITOR DE PLACAS DEBIAN
===========================================

Esta pasta é usada para testar o funcionamento do leitor de placas.

ESTRUTURA SIMPLES:
- {pasta_teste}/
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

Criado em: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
""")
            print(f"[TESTE] Arquivo README criado: {readme_path}")
        
        return True
        
    except Exception as e:
        print(f"[ERRO] Falha ao criar estrutura de teste: {e}")
        return False


def detectar_modo_teste():
    """
    Detecta se deve rodar em modo teste baseado na existência de imagens na pasta teste.
    Retorna True se houver imagens para testar, False caso contrário.
    """
    if not os.path.exists(pasta_teste):
        return False
    
    # Procura por imagens diretamente na pasta teste (estrutura simples)
    try:
        files = os.listdir(pasta_teste)
        for arquivo in files:
            if arquivo.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and arquivo != 'README.txt':
                return True
    except Exception as e:
        print(f"[WARN] Erro ao verificar pasta teste: {e}")
    
    return False


def processar_pasta_teste():
    """
    Processa especificamente a pasta de teste simples.
    Retorna número de arquivos processados.
    """
    arquivos_processados = 0
    print(f"[TESTE] Iniciando processamento da pasta de teste: {pasta_teste}")
    
    try:
        # Lista arquivos diretamente na pasta teste (estrutura simples)
        files = os.listdir(pasta_teste)
        arquivos_imagem = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and f != 'README.txt']
        
        if not arquivos_imagem:
            print("[TESTE] Nenhuma imagem encontrada na pasta de teste.")
            return 0
        
        print(f"[TESTE] Encontradas {len(arquivos_imagem)} imagens para processamento")
        
        for arquivo in arquivos_imagem:
            caminho_arquivo = os.path.join(pasta_teste, arquivo)
            print(f"[TESTE] Processando: {arquivo}")
            
            # Processa a imagem (com deleção)
            sucesso = processar_imagem_teste(caminho_arquivo)
            if sucesso:
                arquivos_processados += 1
                
    except Exception as e:
        print(f"[ERRO] Erro durante processamento de teste: {e}")
    
    return arquivos_processados


def processar_imagem_teste(caminho_arquivo):
    """
    Versão de processar_imagem para modo teste.
    DELETA as imagens após processamento conforme solicitado.
    """
    nome = os.path.basename(caminho_arquivo)
    arquivo_processado_com_sucesso = False
    img_carregada = False
    
    print(f"[TESTE] Processando imagem de teste: {nome}")
    
    # Verifica se o arquivo está completo antes de processar
    if not verificar_arquivo_completo(caminho_arquivo, tempo_estabilidade=0.5):  # Tempo menor para teste
        print(f"[TESTE] Arquivo não está pronto: {nome}")
        return False
    
    try:
        # Parse do nome do arquivo (mais flexível para testes)
        frame_nmr = -1
        car_id = -1
        
        # Tenta extrair informações do nome do arquivo
        try:
            if "_" in nome:
                partes = nome.split("_")
                if len(partes) >= 2:
                    # Tenta encontrar números nas partes
                    for parte in partes[1:]:
                        # Remove extensão se necessário
                        parte_limpa = parte.split('.')[0]
                        if parte_limpa.isdigit():
                            if frame_nmr == -1:
                                frame_nmr = int(parte_limpa)
                            elif car_id == -1:
                                car_id = int(parte_limpa)
                                break
        except:
            pass  # Usa valores padrão se não conseguir parsear
        
        # Se não conseguiu parsear, usa valores de teste
        if frame_nmr == -1:
            frame_nmr = 999  # Valor indicativo de teste
        if car_id == -1:
            car_id = 888  # Valor indicativo de teste
        
        print(f"[TESTE] Frame: {frame_nmr}, Car ID: {car_id}")
        
    except Exception as e:
        print(f"[TESTE] Erro ao parsear nome do arquivo '{nome}': {e}")
        frame_nmr = 999
        car_id = 888

    try:
        # Carregar a imagem
        img = cv2.imread(caminho_arquivo, cv2.IMREAD_GRAYSCALE)
        if img is None:
            print(f"[TESTE] Erro: Não foi possível ler a imagem: {nome}")
            # Remove arquivo corrompido
            remover_arquivo_com_retry(caminho_arquivo)
            return True

        img_carregada = True
        print(f"[TESTE] Imagem carregada: {img.shape}")
        
        texto_detectado, confianca_texto_detectado = ler_placas2(img)

        # Libera a imagem da memória
        del img

        # Exibe resultados detalhados para teste
        if texto_detectado is not None and confianca_texto_detectado is not None:
            print(f"[TESTE] ✅ PLACA DETECTADA: {texto_detectado}")
            print(f"[TESTE] 📊 Confiança: {confianca_texto_detectado:.2f}")
            print(f"[TESTE] 🎯 Frame: {frame_nmr}, Car ID: {car_id}")
            
            if confianca_texto_detectado > confianca_gravar_texto:
                print(f"[TESTE] ✅ Confiança acima do mínimo ({confianca_gravar_texto})")
                # Em modo teste, não salva no banco por padrão
                print(f"[TESTE] 💾 Salvamento no banco DESABILITADO (modo teste)")
            else:
                print(f"[TESTE] ⚠️ Confiança abaixo do mínimo ({confianca_gravar_texto})")
        else:
            print(f"[TESTE] ❌ Nenhuma placa detectada em: {nome}")
        
        arquivo_processado_com_sucesso = True
        
    except cv2.error as e_cv:
        print(f"[TESTE] Erro OpenCV: {e_cv}")
        arquivo_processado_com_sucesso = True
    except Exception as e_proc:
        print(f"[TESTE] Erro inesperado: {e_proc}")
        arquivo_processado_com_sucesso = True
    finally:
        # DELETA os arquivos após processamento conforme solicitado
        if img_carregada or arquivo_processado_com_sucesso:
            sucesso_remocao = remover_arquivo_com_retry(caminho_arquivo)
            if sucesso_remocao:
                print(f"[TESTE] �️ Arquivo de teste removido: {nome}")
            else:
                print(f"[TESTE] ❌ Falha ao remover arquivo de teste: {nome}")
        
        gc.collect()
    
    return arquivo_processado_com_sucesso


def main():
    # Arquivos ignorados adaptados para Linux (sem .crdownload que é específico do Chrome/Windows)
    arquivos_ignorados = {".tmp", ".part", ".lock", ".swp", ".~"}
    print("[INFO] Iniciando leitor de placas (versão Debian/Linux)...")
    print(f"[INFO] Monitorando pasta: {pasta_base}")
    print(f"[INFO] Confiança mínima para gravação: {confianca_gravar_texto}")

    # Cria a pasta base se necessário
    if not criar_pasta_base():
        print("[ERRO] Não foi possível configurar a pasta base. Encerrando.")
        return

    # Cria estrutura de teste
    criar_estrutura_teste()
    
    # Verifica se está em modo teste
    modo_teste = detectar_modo_teste()
    if modo_teste:
        print("🧪 [TESTE] Modo teste detectado! Processando imagens de teste...")
        arquivos_processados = processar_pasta_teste()
        print(f"🧪 [TESTE] Concluído! {arquivos_processados} arquivos processados.")
        print("🧪 [TESTE] Para teste contínuo, o monitoramento normal continuará...")
        print("=" * 60)

    processed_files_in_current_run = set()  # Para evitar reprocessar arquivos já vistos nesta execução
    ultima_limpeza = datetime.now()
    intervalo_limpeza = timedelta(hours=6)  # Limpeza a cada 6 horas

    try:
        while True:
            encontrou_novos_arquivos = False
            
            # Garante que a pasta base existe
            if not os.path.exists(pasta_base):
                print(f"[ERRO] Pasta base {pasta_base} não encontrada. Aguardando...")
                time.sleep(30)  # Espera mais se a pasta base sumir
                continue

            # Listar datas (subpastas)
            try:
                subpastas_data = sorted(
                    [d for d in os.listdir(pasta_base) if os.path.isdir(os.path.join(pasta_base, d))]
                )
            except (FileNotFoundError, PermissionError) as e:
                print(f"[WARN] Problema ao acessar pasta base {pasta_base}: {e}. Tentando novamente.")
                time.sleep(5)
                continue

            # Verifica pasta teste separadamente (estrutura simples)
            if os.path.exists(pasta_teste):
                try:
                    arquivos_teste = [f for f in os.listdir(pasta_teste) 
                                    if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and f != 'README.txt']
                    
                    for nome_arquivo in arquivos_teste:
                        caminho_arquivo = os.path.join(pasta_teste, nome_arquivo)
                        
                        if caminho_arquivo in processed_files_in_current_run:
                            continue  # Já processado nesta sessão
                        
                        print(f"[TESTE] Processando arquivo de teste: {nome_arquivo}")
                        sucesso_processamento = processar_imagem_teste(caminho_arquivo)
                        
                        if sucesso_processamento:
                            processed_files_in_current_run.add(caminho_arquivo)
                            encontrou_novos_arquivos = True
                        else:
                            print(f"[TESTE] Falha no processamento de {nome_arquivo}")
                            
                except Exception as e:
                    print(f"[WARN] Erro ao processar pasta teste: {e}")

            # Processa pastas de dados normais

            for data_dir in subpastas_data:
                pasta_data = os.path.join(pasta_base, data_dir)

                try:
                    # Ordenar por data de modificação para processar os mais antigos primeiro
                    arquivos_na_pasta = sorted(
                        [
                            f
                            for f in os.listdir(pasta_data)
                            if os.path.isfile(os.path.join(pasta_data, f))
                            and not any(f.endswith(ext) for ext in arquivos_ignorados)
                            and not f.startswith(".")  # Ignora arquivos ocultos do Linux
                            and not f.startswith("~")  # Ignora arquivos temporários
                        ],
                        key=lambda x: os.path.getmtime(os.path.join(pasta_data, x)),
                    )
                except (FileNotFoundError, PermissionError) as e:
                    print(f"[WARN] Problema ao acessar subpasta {pasta_data}: {e}. Pulando.")
                    continue  # Pula para a próxima subpasta_data

                for nome_arquivo in arquivos_na_pasta:
                    caminho_arquivo = os.path.join(pasta_data, nome_arquivo)

                    if caminho_arquivo in processed_files_in_current_run:
                        continue  # Já processado nesta sessão

                    # Checagem adicional de arquivo temporário (Linux específico)
                    if (nome_arquivo.startswith(".") or 
                        nome_arquivo.endswith(".lock") or
                        nome_arquivo.endswith(".tmp") or
                        nome_arquivo.endswith(".swp")):
                        print(f"[INFO] Ignorando arquivo temporário: {nome_arquivo}")
                        continue

                    print(f"[INFO] Processando arquivo: {nome_arquivo}")
                    
                    # Usa processamento normal para arquivos da pasta base
                    sucesso_processamento = processar_imagem(caminho_arquivo)
                    
                    if sucesso_processamento:
                        processed_files_in_current_run.add(caminho_arquivo)  # Adiciona ao set de processados apenas se sucesso
                        encontrou_novos_arquivos = True
                    else:
                        print(f"[WARN] Falha no processamento de {nome_arquivo}, será tentado novamente")
                    
                    # Pequena pausa para não sobrecarregar I/O ou CPU no Linux
                    time.sleep(0.05)  # Pausa menor no Linux que geralmente tem I/O mais rápido

            # Se não encontrou novos arquivos, descarrega o buffer e espera mais tempo
            if not encontrou_novos_arquivos:
                flush_buffer_leituras()  # Garante que o buffer seja salvo antes de uma longa espera
                # print("[INFO] Nenhum arquivo novo encontrado. Aguardando...")
                time.sleep(10)  # Tempo de espera original
            else:
                # Se encontrou arquivos, pode ser que haja mais chegando, espera um pouco menos
                # ou apenas continua o loop para verificar rapidamente.
                # flush_buffer_leituras() # Salva o que tiver no buffer após um ciclo de processamento
                time.sleep(1)  # Espera curta se houve processamento

            # Limpeza periódica de arquivos órfãos
            agora = datetime.now()
            if agora - ultima_limpeza > intervalo_limpeza:
                print("[INFO] Iniciando limpeza de arquivos órfãos...")
                limpar_arquivos_antigos(pasta_base, idade_maxima_horas=24)
                ultima_limpeza = agora

            # Limpar o set de arquivos processados periodicamente para evitar consumo excessivo de memória
            # se o script rodar por muitos dias e processar milhões de arquivos únicos.
            if len(processed_files_in_current_run) > 10000:  # Ajuste este número conforme necessário
                print("[INFO] Limpando cache de nomes de arquivos processados.")
                processed_files_in_current_run.clear()
                gc.collect()

    except KeyboardInterrupt:
        print("\n[INFO] Interrupção pelo usuário detectada (Ctrl+C). Finalizando...")
    except Exception as e_main:
        print(f"[ERRO_FATAL] Erro inesperado no loop principal: {e_main}")
    finally:
        print("[INFO] Finalizando o programa. Salvando leituras pendentes e fechando conexão com DB.")
        close_db_connection()  # Garante que tudo seja salvo e a conexão fechada
        print("[INFO] Programa finalizado.")


# Handler para sinais de terminação (funcionamento padrão no Linux)
def signal_handler(signum, frame):
    print(f"[INFO] Sinal {signum} recebido. Finalizando graciosamente...")
    # Isso vai quebrar o loop while True e ir para o finally block
    raise KeyboardInterrupt  # Reutiliza a lógica de KeyboardInterrupt para limpeza


if __name__ == "__main__":
    # Registrar handlers para SIGINT (Ctrl+C) e SIGTERM (finalização)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # No Linux, também podemos capturar SIGHUP (hangup)
    signal.signal(signal.SIGHUP, signal_handler)
    
    main()
