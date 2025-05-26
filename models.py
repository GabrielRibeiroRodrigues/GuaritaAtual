from typing import Any
from django.db import models


class Leitura_placa(models.Model):
    frame_nmr = models.IntegerField(verbose_name='Número do Frame')
    car_id = models.IntegerField(verbose_name='ID do Veículo')
    license_number = models.CharField(max_length=8, verbose_name='Placa')
    license_number_score = models.FloatField(verbose_name='Precisão')
    data_hora = models.DateTimeField(auto_now_add=True, verbose_name='Data e Hora')
    class Meta:
        verbose_name = 'Leitura de Placa'
        verbose_name_plural = 'Leitura de Placas'

    def __str__(self):
        return self.id


class Marca(models.Model):
    marca = models.CharField(max_length = 20, verbose_name = 'marca',blank = True, null = True)
class Modelo(models.Model):
    modelo = models.CharField(max_length = 20, verbose_name = 'modelo',blank = True, null = True)
class Cor(models.Model):
    cor = models.CharField(max_length = 20, verbose_name = 'cores', blank = True, null = True)

class Combustivel(models.Model):
     combustivel = models.CharField(max_length = 30, verbose_name = 'comb', blank = True, null = True)

class Veiculo(models.Model): 
    proprietario = models.CharField(max_length=100, verbose_name='Proprietario') 
    placa = models.CharField(max_length=8, verbose_name='Placa')
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, verbose_name="modelo", blank = True, null = True)
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, verbose_name="marca", blank = True, null = True)
    cor = models.ForeignKey(Cor, on_delete = models.CASCADE, verbose_name = 'cores',blank = True, null = True )     
    ano = models.IntegerField(null = True)
    combustivel = models.ForeignKey(Combustivel, on_delete = models.CASCADE, verbose_name = 'comb', blank = True, null = True)
    renavam = models.IntegerField(null = True)
    chassi = models.CharField(max_length=17, verbose_name='chassi', blank = True, null = True)
     

    class Meta:
        verbose_name = 'Placa Cadastrada'
        verbose_name_plural = 'Placas Cadastradadas'

    def __str__(self):
        return self.id

class Registro_Entrada_Saida(models.Model):
    id_veiculo = models.IntegerField(blank = True, null = True)
    data = models.DateTimeField()
    tipo = models.CharField(max_length=7, verbose_name='tipo')

class camera(models.Model):
    modelo = models.CharField(max_length=30, verbose_name='modelo')
    marca = models.CharField(max_length=30, verbose_name='marca')
    porta = models.IntegerField()
    local_instalacao = models.CharField(max_length=100, verbose_name='local_install')
    entradas = models.CharField(max_length=100, verbose_name='entradas')
    ip =  models.CharField(max_length=100, verbose_name='ip', default = 'default ip', blank = True)
    data_aquisicao = models.DateField(blank = True,null = True)
    data_instalacao = models.DateField(blank = True, null = True)

class Veiculos_sem_autorizacao(models.Model):
    placa_ex  = models.CharField(max_length = 7, verbose_name = 'veiculos_sem_autorizacao',blank = True, null = True)

    
