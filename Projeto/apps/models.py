from django.db import models
from django.contrib.auth.models import User
from datetime import datetime

# Create your models here.

# lembrando: SEMPRE que modificar ou acrescentar uma models a gnt tem q fazer os comandos:
# python manage.py makemigrations
# e em seguida:
# python manage.py migrate
# python manage.py runserver

class Perfil(models.Model):
    nome = models.CharField(max_length=255)
    username = models.CharField(max_length=30, unique=True)
    cpf = models.CharField(max_length=11)
    contato = models.CharField(max_length=11)

    funcionario = models.BooleanField()  # Campo booleano para distinguir entre cliente e funcionário

    def delete(self, *args, **kwargs):
        # Atualiza as tarefas antes de deletar o perfil
        OrdemServico.objects.filter(funcionario_responsavel=self).update(funcionario_responsavel=None, status='Enviada')
        super().delete(*args, **kwargs)


    def __str__(self):
        return (self.nome)


class OrdemServico(models.Model):
    STATUS_CHOICES = [
        ('Enviada', 'Ordem de serviço enviada'),
        ('Iniciada', 'Ordem de serviço iniciada'),
        ('Em_analise', 'Em análise'),
        ('Aguardando_peca', 'Aguardando peça'),
        ('Aguardando_reparo', 'Aguardando reparo'),
        ('Em_reparo', 'Em reparo'),
        ('Pronto', 'Pronto'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Enviada')

    TIPOS_ATENDIMENTO = [
        ('-', '-'),
        ('FON', 'Fora on site'),
        ('FB', 'Fora Balcão'),
        ('GS', 'Garantia serviço'),
        ('GB', 'Garantia balcão'),
        ('GON', 'Garantia on site'),
        ('GIN', 'Garantia instalação'),
        ('GRIN', 'Garantia reincidência'),
    ]
    tipo_atendimento = models.CharField(max_length=4, choices=TIPOS_ATENDIMENTO, default='-')

    aparelho = models.CharField(max_length=255)
    modelo = models.CharField(max_length=255)
    garantia = models.BooleanField(choices=[(True, 'Sim'), (False, 'Não')])
    descricao_problema = models.CharField(max_length=255)
    perfil_os = models.ForeignKey('Perfil', on_delete=models.CASCADE, default=None)
    imagem = models.ImageField(upload_to='picture/', blank=True, null=True)
    avaliacao = models.IntegerField(blank=True, null=True)
    comentario_avaliacao = models.TextField(blank=True, null=True)

    funcionario_responsavel = models.ForeignKey('Perfil', on_delete=models.SET_NULL, null=True, blank=True, related_name='ordens_responsavel')

    mensagem_funcionario = models.TextField(blank=True, null=True)
    problema_detectado = models.TextField(blank=True, null=True)

    numero = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(default=datetime.now)  # Adiciona o campo de data de criação com um valor padrão

    def save(self, *args, **kwargs):
        if not self.numero:
            year = datetime.now().year
            prefix = str(year)[-2:]
            last_order = OrdemServico.objects.filter(numero__startswith=prefix).order_by('-numero').first()
            if last_order:
                last_number = int(last_order.numero[-3:])
                new_number = last_number + 1
            else:
                new_number = 1
            self.numero = f"{prefix}{new_number:03d}"
        super().save(*args, **kwargs)

    def detalhes(self):
        return {
            'aparelho': self.aparelho,
            'modelo': self.modelo,
            'garantia': 'Sim' if self.garantia else 'Não',
            'descricao_problema': self.descricao_problema,
            'cliente_nome': self.perfil_os.username if self.perfil_os else None,
            'cliente_cpf': self.perfil_os.cpf if self.perfil_os else None,
            'cliente_contato': self.perfil_os.contato if self.perfil_os else None,
            'status': self.get_status_display(),
            'mensagem_funcionario': self.mensagem_funcionario,
            'problema_detectado': self.problema_detectado,
            'tipo_atendimento': self.get_tipo_atendimento_display(),
        }

    def __str__(self):
        return self.aparelho