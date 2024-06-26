from django.shortcuts import render, redirect,  get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils.dateparse import parse_date
from .utils import filtrar_ordens
from .models import *
from django.contrib import auth
from django.http import HttpResponse
from notifications.signals import notify
from notifications.models import Notification
from django.http import HttpResponseForbidden
from django.db import IntegrityError
import re


# VIEWS DE LOGIN
def login_view(request):
    if request.method == 'POST':
        tipo_usuario = request.POST.get('tipo_usuario')

        if tipo_usuario == 'cliente':
            return redirect("cliente_login")
        elif tipo_usuario == 'funcionario':
            return redirect("funcionario_login")

    return render(request, 'apps/login.html')

def logout_view(request):
    logout(request)
    if "usuario" in request.session:
        del request.session["usuario"]
    return redirect('login')

def cliente_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        senha = request.POST['senha']

        user = authenticate(username=username, password=senha)
        if user is not None:
            perfil = Perfil.objects.get(username=user.username)
            if perfil.funcionario:
                messages.error(request, 'Erro: Funcionário não pode acessar como cliente.')
                return redirect('login')
            else:
                login(request, user)
                return redirect('home_cliente')
        else:
            messages.error(request, 'Erro ao autenticar o cliente. Por favor, tente novamente.')
            return redirect('cliente_login')

    return render(request, 'apps/cliente_login.html')

def funcionario_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        senha = request.POST['senha']

        user = authenticate(username=username, password=senha)
        if user is not None:
            perfil = Perfil.objects.get(username=user.username)
            if not perfil.funcionario:
                messages.error(request, 'Erro: Cliente não pode acessar como funcionário.')
                return redirect('login')
            else:
                login(request, user)
                return redirect('servicos')
        else:
            messages.error(request, 'Erro ao autenticar o funcionário. Por favor, tente novamente.')
            return redirect('funcionario_login')

    return render(request, 'apps/funcionario_login.html')

def cliente_cadastro(request): 
    if request.method == 'POST':
        username = request.POST['username']
        nome = request.POST['nome']
        cpf = request.POST['cpf']
        email = request.POST['email']
        senha = request.POST['senha']
        confirmar_senha = request.POST['confirmar_senha']
        contato = request.POST['contato']

        if senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem. Por favor, tente novamente.')
            return render(request, 'apps/cliente_cadastro.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe')
            return render(request, 'apps/cliente_cadastro.html')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email já está sendo usado')
            return render(request, 'apps/cliente_cadastro.html')
        
        errors = validate_dados(nome, username, email, cpf, contato)

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'apps/cliente_cadastro.html')

        try:
            user = User.objects.create_user(username=username, email=email, password=senha)
            Perfil.objects.create(username=username, funcionario=0, cpf=cpf, contato=contato, nome=nome)
            login(request, user)
            request.session["usuario"] = username
            return redirect('home_cliente')
        except IntegrityError:
            messages.error(request, 'Erro ao criar usuário. Por favor, tente novamente.')
            return render(request, 'apps/cliente_cadastro.html')

    return render(request, 'apps/cliente_cadastro.html')

def funcionario_cadastro(request): 
    if request.method == "POST":
        username = request.POST['username']
        nome = request.POST['nome']
        email = request.POST['email']
        senha = request.POST['senha']
        confirmar_senha = request.POST['confirmar_senha']

        if senha != confirmar_senha:
            messages.error(request, 'As senhas não coincidem. Por favor, tente novamente.')
            return render(request, 'apps/funcionario_cadastro.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Usuário já existe')
            return render(request, 'apps/funcionario_cadastro.html')
        elif User.objects.filter(email=email).exists():
            messages.error(request, 'Email já está sendo usado')
            return render(request, 'apps/funcionario_cadastro.html')
        
        errors = validate_dados(nome, username, email)

        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'apps/funcionario_cadastro.html')
        
        try:
            user = User.objects.create_user(username=username, email=email, password=senha)
            Perfil.objects.create(username=username, funcionario=1, nome=nome)
            login(request, user)
            request.session["usuario"] = username
            return redirect('servicos')
        except IntegrityError:
            messages.error(request, 'Erro ao criar usuário. Por favor, tente novamente.')
            return render(request, 'apps/funcionario_cadastro.html')

    return render(request, 'apps/funcionario_cadastro.html')

# FINAL DAS VIEWS DE LOGIN

# FUNÇÕES DA CONTA CLIENTE
@login_required
def cliente_perfil(request):
    user = request.user
    try:
        usuario = Perfil.objects.get(username=user.username)
    except Perfil.DoesNotExist:
        return redirect('login')

    if usuario.funcionario == 1:
        return redirect('login')
    else:
        context = {
            'nome_completo': usuario.nome,
            'email': user.email,
            'cpf': usuario.cpf,
            'contato': usuario.contato
        }
        return render(request, 'apps/cliente_perfil.html', context)

@login_required
def cliente_editar_perfil(request):
    try:
        # Tenta recuperar o perfil baseado no nome de usuário associado ao usuário atual.
        usuario = Perfil.objects.get(username=request.user.username)
    except Perfil.DoesNotExist:
        # Se o perfil não existir, opcionalmente, redirecione ou exiba uma mensagem.
        messages.error(request, 'Perfil não encontrado.')
        return redirect('alguma_url_de_fallback')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        contato = request.POST.get('contato')
        email = request.POST.get('email')

        user = request.user
        user.email = email
        user.save()

        # Atualiza o perfil do usuário com as novas informações.
        usuario.nome = nome
        usuario.cpf = cpf
        usuario.contato = contato
        usuario.save()

        # Mensagem de sucesso após salvar as alterações.
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('cliente_perfil')

    return render(request, 'apps/cliente_editar_perfil.html', {'perfil': usuario})

@login_required
def home_cliente(request):
    user = request.user
    usuario = Perfil.objects.get(username=user.username)

    if usuario.funcionario == 1:
        return redirect(login)
    else:
        if request.user.is_anonymous:
            return redirect(login)
        else:
            ordens = OrdemServico.objects.filter(perfil_os=usuario)
            return render(request, 'apps/home_cliente.html', {'ordens': ordens})


@login_required
def cadastrar_os_cliente(request):
    user = request.user
    usuario = Perfil.objects.get(username=user.username)

    if usuario.funcionario == 1:
        return redirect(login)
    else:
        if request.method == 'POST':
            aparelho = request.POST['aparelho']
            garantia = request.POST['garantia'] == 'True'
            modelo = request.POST['modelo']
            descricao_problema = request.POST['descricao_problema']
            imagem = request.FILES.get('picture__input')  # Obtém a imagem do formulário

            # Cria uma nova OrdemServico associada ao perfil do usuário logado
            OrdemServico.objects.create(
                aparelho=aparelho,
                modelo=modelo,
                garantia=garantia,
                descricao_problema=descricao_problema,
                perfil_os=usuario,
                imagem=imagem  # Adiciona a imagem ao objeto OrdemServico
            )

            return redirect(home_cliente)

        return render(request, 'apps/cadastrar_os_cliente.html')
    
@login_required
def avaliar_os(request, os_id):
    os = get_object_or_404(OrdemServico, id=os_id)
    if request.method == 'POST':
        avaliacao = request.POST.get('avaliacao')
        comentario_avaliacao = request.POST.get('comentario_avaliacao')

        if avaliacao.strip() and avaliacao.isdigit():
            avaliacao = int(avaliacao)
            if 1 <= avaliacao <= 5:
                os.avaliacao = avaliacao
                os.comentario_avaliacao = comentario_avaliacao
                os.save()
                messages.success(request, 'Avaliação salva com sucesso!')
                return redirect('detalhes_os', os_id=os.id)
            else:
                messages.error(request, 'Avaliação fora do intervalo permitido (1-5).')
        else:
            messages.error(request, 'Avaliação não é um número inteiro ou está vazia.')

    context = {
        'os': os,
        'avaliacao': os.avaliacao,
        'comentario_avaliacao': os.comentario_avaliacao
    }
    return render(request, 'apps/avaliar_os.html', context)

@login_required
def lista_notifications(request):
    user = request.user
    usuario = Perfil.objects.get(username=user.username)

    if usuario.funcionario == 1:
        return redirect(login)
    else:
        if request.user.is_anonymous:
            return redirect(login)
        else:
            notifications = request.user.notifications.unread()
            context = {
                'notifications': notifications,
            }
            return render(request, 'apps/lista_notifications.html', context)

#FINAL DAS VIEWS DA CONTA CLIENTE


# VIEWS DO FUNCIONÁRIO
@login_required
def funcionario_perfil(request):
    user = request.user
    usuario = get_object_or_404(Perfil, username=user.username)

    if usuario.funcionario == 0:
        return redirect('login')
    else:
        context = {
            'nome_completo': usuario.nome,
            'email': user.email,  # Passa o email do objeto User associado
            'cpf': usuario.cpf,
            'contato': usuario.contato,
            'funcionario': 1  # Assegura que o menu lateral de funcionário seja exibido
        }
        return render(request, 'apps/funcionario_perfil.html', context)

@login_required
def funcionario_editar_perfil(request):
    user = request.user
    perfil = get_object_or_404(Perfil, username=user.username)

    if perfil.funcionario == 0:
        return redirect('login')

    if request.method == 'POST':
        nome = request.POST.get('nome')
        cpf = request.POST.get('cpf')
        contato = request.POST.get('contato')
        email = request.POST.get('email')

        if email:
            user.email = email
            user.save()

        if nome:
            perfil.nome = nome
        if cpf:
            perfil.cpf = cpf
        if contato:
            perfil.contato = contato

        perfil.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('funcionario_perfil')
    else:
        context = {
            'perfil': perfil,
            'user': user,
            'funcionario': 1  # Indica que o usuário é um funcionário
        }
        return render(request, 'apps/funcionario_editar_perfil.html', context)


@login_required
def servicos(request):
    user = request.user
    usuario = Perfil.objects.get(username=user.username)

    if usuario.funcionario == 0:
        return redirect(login)
    else:
        # colocar aq a opção de filter o que ele editou
        ordens_servico = OrdemServico.objects.filter(funcionario_responsavel=usuario)
        return render(request, 'apps/servicos.html', {'funcionario': 1, 'ordens_servico': ordens_servico})

@login_required
def listar_os(request):
    user = request.user
    try:
        usuario = Perfil.objects.get(username=user.username)
    except Perfil.DoesNotExist:
        usuario = None

    if usuario is None or usuario.funcionario == 0:
        return redirect('login')
    else:
        ordens = OrdemServico.objects.all()
        ordens, status, data_criacao = filtrar_ordens(request, ordens)
        return render(request, 'apps/listar_os.html', {
            'funcionario': 1,
            'ordens': ordens,
            'status': status,
            'data_criacao': data_criacao,
            'usuario': usuario  # Passa o perfil do usuário logado para o contexto
        })


@login_required
def editar_os(request, os_id):
    os = get_object_or_404(OrdemServico, id=os_id)
    user = request.user
    usuario = Perfil.objects.get(username=user.username)

    if usuario.funcionario == 0:
        return redirect(login)
    else:
        if os.funcionario_responsavel != usuario:
            return redirect('detalhes_os', os_id=os.id)

        if request.method == 'POST':
            os.status = request.POST.get('status')
            os.mensagem_funcionario = request.POST.get('mensagem_funcionario')
            os.problema_detectado = request.POST.get('problema_detectado')
            os.tipo_atendimento = request.POST.get('tipo_atendimento')
            os.save()
            return redirect('detalhes_os', os_id=os.id)
    context = {
            'funcionario': 1, 
            'os': os, 
        }
    return render(request, 'apps/editar_os.html', context)

@login_required
def excluir_os(request, pk):
    os = get_object_or_404(OrdemServico, pk=pk)

    # Verifica se há um funcionário responsável pela OS
    if not os.funcionario_responsavel:
        return HttpResponseForbidden("Não é possível excluir uma OS sem um funcionário responsável.")

    # Verifica se o usuário logado é o funcionário responsável pela OS
    if os.funcionario_responsavel.username != request.user.username:
        return HttpResponseForbidden("Você não tem permissão para excluir esta OS.")

    if request.method == 'POST':
        os.delete()
        return redirect('listar_os')  # Redireciona para a lista de OS após a exclusão

    return render(request, 'excluir_os.html', {'os': os})

# FINAL DAS FUNÇÕES DO FUNCIONÁRIO


# VIEW DOS DOIS
@login_required
def detalhes_os(request, os_id):
    user = request.user
    usuario = Perfil.objects.get(username=user.username)
    os = get_object_or_404(OrdemServico, id=os_id)
    detalhes_da_os = os.detalhes()
    numero_os = os.numero

    if usuario.funcionario == 1:
        # Lógica para funcionários
        if request.method == 'POST':
            if os.status == 'Enviada' and 'responsabilizar' in request.POST:
                os.funcionario_responsavel = usuario
                os.status = 'Iniciada'
                os.save()

            # Verifica se o formulário de atualização do status foi submetido
            if 'atualizar_status' in request.POST:
                # Atualiza o status da ordem de serviço com base no valor selecionado no formulário
                novo_status = request.POST.get('status')
                os.status = novo_status
                # Salva as alterações na ordem de serviço
                os.descricao_problema = request.POST.get('descricao_problema')
                os.mensagem_funcionario = request.POST.get('mensagem_funcionario')
                os.problema_detectado = request.POST.get('problema_detectado')
                os.tipo_atendimento = request.POST.get('tipo_atendimento')  # Atualiza o tipo de atendimento
                os.save()

        # Adicione o nome do funcionário responsável ao contexto
        funcionario_responsavel = os.funcionario_responsavel.username if os.funcionario_responsavel else None

        context = {
            'funcionario': 1, 
            'os': os, 
            'detalhes_da_os': detalhes_da_os, 
            'funcionario_responsavel': funcionario_responsavel,
            'numero_os': numero_os,
        }

        return render(request, 'apps/detalhes_os.html', context)

    else:
        # Lógica para clientes
        context = {
            'funcionario': 0, 
            'os': os, 
            'detalhes_da_os': detalhes_da_os, 
            'numero_os': numero_os,
        }
        return render(request, 'apps/detalhes_os_cliente.html', context)

@login_required
def excluir_conta(request):
    usuario = Perfil.objects.get(username=request.user.username)

    if request.method == 'POST':
        usuario.delete()
        request.user.delete()
        return redirect('login')
    
    if usuario.funcionario == 0:
        return render(request, 'apps/excluir_conta.html')
    else:
        return render(request, 'apps/excluir_conta.html', {'funcionario': 1})

def validate_dados(nome, username, email, cpf=None, contato=None):
    errors = []

    if not nome or len(nome) < 2:
        errors.append("O nome deve ter pelo menos dois caracteres.")

    if not username or len(username) < 3:
        errors.append("O username deve ter pelo menos três caracteres.")

    if email and not re.match(r'^[\w\.-]+@[\w\.-]+$', email):
        errors.append("O email deve estar em um formato válido.")

    if cpf is not None and len(cpf) != 11 and not cpf.isdigit():
        errors.append("O CPF deve ter 11 dígitos numéricos.")

    if contato is not None and len(contato) != 11 and not contato.isdigit():
        errors.append("O contato deve ter 11 dígitos numéricos.")

    return errors