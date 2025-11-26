import os
import secrets
import string
import collections
import locale 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from functools import wraps
from dotenv import load_dotenv
from models import db, User, Produto, Cupom, Pedido, ItensPedido, ItemCarrinho
from sqlalchemy import or_, func
from decimal import Decimal

# --- CONFIGURAÇÃO INICIAL ---
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Você precisa estar logado para acessar esta página.'
login_manager.login_message_category = 'info'

# --- CONFIGURAÇÃO DE MOEDA (LOCALE) ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
    except locale.Error:
        locale.setlocale(locale.LC_ALL, '')
        print("Aviso: Locale 'pt_BR' não encontrado. Formatando com o padrão do sistema.")

@app.template_filter('currency')
def format_currency(value):
    """Formata um valor (Decimal ou float) como moeda BRL."""
    if value is None:
        return "R$ 0,00"
    try:
        return locale.currency(float(value), grouping=True, symbol='R$')
    except (TypeError, ValueError):
        return str(value)

# --- GERENCIAMENTO DE LOGIN ---
@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id_usuario=int(user_id)).first()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.tipo_usuario != 'admin':
            flash('Acesso restrito a administradores.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

def seller_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or (current_user.tipo_usuario not in ['admin', 'vendedor']):
            flash('Acesso restrito a vendedores.', 'danger')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        senha = request.form.get('senha')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(senha):
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Email ou senha inválidos.', 'danger')

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        tipo_usuario = request.form.get('tipo_usuario', 'cliente') 

        if tipo_usuario not in ['cliente', 'vendedor']:
             tipo_usuario = 'cliente'

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('register'))

        new_user = User(nome=nome, email=email, senha=senha, tipo_usuario=tipo_usuario)
        db.session.add(new_user)
        db.session.commit()
        
        new_user.id_usuario = new_user.id
        db.session.commit()

        flash('Conta criada com sucesso! Faça o login.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('cupom_codigo', None)
    logout_user()
    flash('Você saiu da sua conta.', 'info')
    return redirect(url_for('home'))

# --- ROTAS DE PERFIL E SENHA ---
@app.route('/meu-perfil', methods=['GET', 'POST'])
@login_required
def meu_perfil():
    user = current_user
    
    if request.method == 'POST':
        user.nome = request.form.get('nome')
        novo_email = request.form.get('email')
        
        if novo_email != user.email:
            email_existente = User.query.filter_by(email=novo_email).first()
            if email_existente:
                flash('Este e-mail já está em uso por outra conta.', 'danger')
                return redirect(url_for('meu_perfil'))
            user.email = novo_email
            flash('E-mail atualizado com sucesso.', 'success')

        senha_atual = request.form.get('senha_atual')
        nova_senha = request.form.get('nova_senha')
        confirmar_senha = request.form.get('confirmar_senha')

        if nova_senha:
            if not user.check_password(senha_atual):
                flash('Sua senha atual está incorreta. A senha não foi alterada.', 'danger')
                return redirect(url_for('meu_perfil'))
            
            if nova_senha != confirmar_senha:
                flash('As novas senhas não coincidem. A senha não foi alterada.', 'danger')
                return redirect(url_for('meu_perfil'))
            
            user.set_password(nova_senha)
            flash('Senha alterada com sucesso!', 'success')
        
        db.session.commit()
        
        if not nova_senha:
            flash('Perfil atualizado com sucesso!', 'success')
            
        return redirect(url_for('meu_perfil'))

    return render_template('meu_perfil.html')

# --- ROTAS PRINCIPAIS (E-COMMERCE) ---

@app.route('/')
def home():
    # 1. Novidades (10 mais recentes)
    produtos_recentes = Produto.query.order_by(Produto.data_cadastro.desc()).limit(10).all()
    
    # ========================================
    #           (SQL CORRIGIDO)
    # Adicionadas todas as colunas de Produto ao GROUP BY
    # ========================================
    query_mais_vendidos = db.session.query(
        Produto, func.sum(ItensPedido.quantidade).label('total_vendido')
    ).join(
        ItensPedido, Produto.id_produto == ItensPedido.id_produto
    ).group_by(
        Produto.id_produto,
        Produto.id_vendedor,
        Produto.nome,
        Produto.descricao,
        Produto.preco,
        Produto.estoque,
        Produto.categoria,
        Produto.url_imagem,
        Produto.data_cadastro
    ).order_by(
        func.sum(ItensPedido.quantidade).desc()
    ).limit(10).all()
    
    mais_vendidos = [produto for produto, total in query_mais_vendidos]

    # 3. Categoria Específica (Relógios de Luxo)
    relogios_luxo = Produto.query.filter(
        Produto.categoria.startswith('Relógios de Luxo')
    ).order_by(Produto.data_cadastro.desc()).limit(10).all()

    # 4. Em Destaque (10 com mais estoque)
    produtos_destaque = Produto.query.order_by(Produto.estoque.desc()).limit(10).all()

    return render_template('home.html', 
                           produtos_recentes=produtos_recentes,
                           mais_vendidos=mais_vendidos,
                           relogios_luxo=relogios_luxo,
                           produtos_destaque=produtos_destaque
                           )


@app.route('/catalogo')
def catalogo():
    categoria = request.args.get('categoria')
    query = Produto.query
    
    if categoria:
        query = query.filter(Produto.categoria.startswith(categoria))
    
    todos_produtos = query.order_by(Produto.nome).all()
    
    categorias_db = db.session.query(Produto.categoria).distinct().all()
    categorias_set = set()
    for cat_tuple in categorias_db:
        if cat_tuple[0]:
            primeira_categoria = cat_tuple[0].split('/')[0].strip()
            if primeira_categoria:
                categorias_set.add(primeira_categoria)
    
    categorias = sorted(list(categorias_set))
    
    return render_template('catalogo.html', 
                           produtos=todos_produtos, 
                           categorias=categorias, 
                           categoria_selecionada=categoria)

@app.route('/produto/<int:id>')
def detalhes(id):
    produto = Produto.query.get_or_404(id)
    return render_template('detalhes.html', produto=produto)

@app.route('/venda')
@login_required
@seller_required
def venda():
    if current_user.tipo_usuario == 'admin':
        produtos_vendedor = Produto.query.order_by(Produto.nome).all()
    else:
        produtos_vendedor = Produto.query.filter_by(id_vendedor=current_user.id_usuario).order_by(Produto.nome).all()
        
    return render_template('venda.html', produtos=produtos_vendedor)

@app.route('/cupons')
def cupons():
    cupons_ativos = Cupom.query.filter_by(ativo=True).all()
    return render_template('cupom.html', cupons=cupons_ativos)

@app.route('/pedidos')
@login_required
def pedidos():
    meus_pedidos = Pedido.query.filter_by(id_usuario=current_user.id_usuario).order_by(Pedido.data_pedido.desc()).all()
    return render_template('pedidos.html', pedidos=meus_pedidos)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/search')
def search():
    query = request.args.get('query')
    if not query:
        flash('Digite algo para pesquisar.', 'info')
        return redirect(request.referrer or url_for('home'))
    
    search_term = f"%{query}%"
    
    produtos_encontrados = Produto.query.filter(
        or_(Produto.nome.ilike(search_term), Produto.descricao.ilike(search_term), Produto.categoria.ilike(search_term))
    ).all()
    
    return render_template('search_results.html', 
                           query=query, 
                           produtos=produtos_encontrados)

# --- ROTAS DO CARRINHO ---

@app.route('/carrinho', methods=['GET', 'POST'])
def carrinho():
    if not current_user.is_authenticated:
        flash('Você precisa estar logado para ver seu carrinho.', 'info')
        return redirect(url_for('login'))

    if request.method == 'POST':
        codigo_cupom = request.form.get('codigo_cupom')
        if not codigo_cupom:
            session.pop('cupom_codigo', None)
            flash('Cupom removido.', 'info')
            return redirect(url_for('carrinho'))

        cupom = Cupom.query.filter_by(codigo=codigo_cupom, ativo=True).first()
        
        if cupom:
            session['cupom_codigo'] = cupom.codigo
            flash(f'Cupom "{cupom.codigo}" aplicado com sucesso!', 'success')
        else:
            flash('Cupom inválido ou expirado.', 'danger')
        return redirect(url_for('carrinho'))

    itens_carrinho = ItemCarrinho.query.filter_by(id_usuario=current_user.id_usuario).all()
    
    subtotal = Decimal('0.00')
    for item in itens_carrinho:
        subtotal += item.produto.preco * item.quantidade
        
    cupom_aplicado = None
    desconto = Decimal('0.00') 
    cupom_codigo_sessao = session.get('cupom_codigo')
    
    if cupom_codigo_sessao:
        cupom_aplicado = Cupom.query.filter_by(codigo=cupom_codigo_sessao, ativo=True).first()
        if cupom_aplicado:
            if cupom_aplicado.tipo == 'porcentagem':
                desconto = (subtotal * cupom_aplicado.valor) / 100
            elif cupom_aplicado.tipo == 'fixo':
                desconto = cupom_aplicado.valor
            
            desconto = min(desconto, subtotal) 
        else:
            session.pop('cupom_codigo', None)
            flash('O cupom aplicado anteriormente não é mais válido.', 'info')

    total = subtotal - desconto

    produtos_recomendados = []
    if itens_carrinho:
        ids_no_carrinho = [item.id_produto for item in itens_carrinho]
        
        categorias_no_carrinho = set()
        for item in itens_carrinho:
            categoria_principal = item.produto.categoria.split('/')[0].strip()
            if categoria_principal:
                categorias_no_carrinho.add(categoria_principal)
        
        if categorias_no_carrinho:
            filtros_categoria = [Produto.categoria.startswith(cat) for cat in categorias_no_carrinho]
            
            produtos_recomendados = Produto.query.filter(
                or_(*filtros_categoria),
                Produto.id_produto.notin_(ids_no_carrinho)
            ).limit(4).all()

    return render_template('carrinho.html', 
                           itens_carrinho=itens_carrinho, 
                           subtotal=subtotal,
                           desconto=desconto,
                           total=total,
                           cupom_aplicado=cupom_aplicado,
                           produtos_recomendados=produtos_recomendados)


@app.route('/add-carrinho', methods=['POST'])
@login_required
def add_carrinho():
    produto_id = request.form.get('produto_id')
    try:
        quantidade = int(request.form.get('quantidade', 1))
        if quantidade <= 0:
            quantidade = 1
    except ValueError:
        quantidade = 1

    produto = Produto.query.get(produto_id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(request.referrer)
        
    item_existente = ItemCarrinho.query.filter_by(
        id_usuario=current_user.id_usuario, 
        id_produto=produto_id
    ).first()
    
    if item_existente:
        item_existente.quantidade += quantidade
        flash(f'Quantidade de "{produto.nome}" atualizada no carrinho!', 'info')
    else:
        novo_item = ItemCarrinho(
            id_usuario=current_user.id_usuario,
            id_produto=produto_id,
            quantidade=quantidade
        )
        db.session.add(novo_item)
        flash(f'"{produto.nome}" adicionado ao carrinho!', 'success')
        
    db.session.commit()
    return redirect(url_for('carrinho'))


@app.route('/remove-carrinho/<int:id_item>', methods=['POST'])
@login_required
def remove_carrinho(id_item):
    item = ItemCarrinho.query.get_or_404(id_item)
    
    if item.id_usuario != current_user.id_usuario:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('carrinho'))
        
    db.session.delete(item)
    db.session.commit()
    flash('Item removido do carrinho.', 'info')
    return redirect(url_for('carrinho'))


@app.route('/update-carrinho/<int:id_item>', methods=['POST'])
@login_required
def update_carrinho(id_item):
    item = ItemCarrinho.query.get_or_404(id_item)
    
    if item.id_usuario != current_user.id_usuario:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('carrinho'))

    try:
        quantidade = int(request.form.get('quantidade'))
        if quantidade <= 0:
            return remove_carrinho(id_item)
        
        if quantidade > item.produto.estoque:
            flash(f'Estoque insuficiente. Temos apenas {item.produto.estoque} unidades.', 'danger')
            return redirect(url_for('carrinho'))
            
        item.quantidade = quantidade
        db.session.commit()
        flash('Quantidade atualizada.', 'info')
        
    except ValueError:
        flash('Quantidade inválida.', 'danger')
        
    return redirect(url_for('carrinho'))


# --- ROTA DE CHECKOUT E DEVOLUÇÃO ---

@app.route('/finalizar-pedido', methods=['POST'])
@login_required
def finalizar_pedido():
    itens_carrinho = ItemCarrinho.query.filter_by(id_usuario=current_user.id_usuario).all()
    
    if not itens_carrinho:
        flash('Seu carrinho está vazio.', 'danger')
        return redirect(url_for('carrinho'))

    # 1. VERIFICAÇÃO DE ESTOQUE
    for item in itens_carrinho:
        if item.quantidade > item.produto.estoque:
            flash(f'Erro: Estoque insuficiente para "{item.produto.nome}". Temos apenas {item.produto.estoque} unidades. Pedido não finalizado.', 'danger')
            return redirect(url_for('carrinho'))

    # 2. CÁLCULO DO TOTAL
    subtotal = Decimal('0.00')
    for item in itens_carrinho:
        subtotal += item.produto.preco * item.quantidade
        
    desconto = Decimal('0.00') 
    cupom_codigo_sessao = session.get('cupom_codigo')
    
    if cupom_codigo_sessao:
        cupom_aplicado = Cupom.query.filter_by(codigo=cupom_codigo_sessao, ativo=True).first()
        if cupom_aplicado:
            if cupom_aplicado.tipo == 'porcentagem':
                desconto = (subtotal * cupom_aplicado.valor) / 100
            elif cupom_aplicado.tipo == 'fixo':
                desconto = cupom_aplicado.valor
            desconto = min(desconto, subtotal)

    total = subtotal - desconto

    # 3. CRIAÇÃO DO PEDIDO
    try:
        novo_pedido = Pedido(
            id_usuario=current_user.id_usuario,
            valor_total=total,
            status='Enviado' 
        )
        db.session.add(novo_pedido)
        db.session.commit() 

        for item in itens_carrinho:
            produto = item.produto 
            
            novo_item_pedido = ItensPedido(
                id_pedido=novo_pedido.id_pedido,
                id_produto=item.id_produto,
                quantidade=item.quantidade,
                preco_unitario=produto.preco 
            )
            
            produto.estoque -= item.quantidade
            
            db.session.add(novo_item_pedido)
            db.session.delete(item) 

        session.pop('cupom_codigo', None)
        
        db.session.commit()

        flash('Pedido finalizado com sucesso!', 'success')
        return redirect(url_for('pedidos'))

    except Exception as e:
        db.session.rollback() 
        flash(f'Ocorreu um erro ao finalizar seu pedido: {e}', 'danger')
        return redirect(url_for('carrinho'))


@app.route('/solicitar-devolucao/<int:id_pedido>', methods=['POST'])
@login_required
def solicitar_devolucao(id_pedido):
    pedido = Pedido.query.get_or_404(id_pedido)

    if pedido.id_usuario != current_user.id_usuario:
        flash('Não foi possível processar sua solicitação.', 'danger')
        return redirect(url_for('pedidos'))

    status_permitidos = ['Enviado', 'Concluido']

    if pedido.status in status_permitidos:
        pedido.status = 'Devolução Solicitada'
        db.session.commit()
        flash(f'Solicitação de devolução para o Pedido #{pedido.id_pedido} foi enviada.', 'success')
    else:
        flash(f'Este pedido não pode ser devolvido (Status: {pedido.status}).', 'info')
        
    return redirect(url_for('pedidos'))


# --- ROTAS DE ADMIN ---
@app.route('/admin')
@login_required
@admin_required
def admin_panel():
    users = User.query.all()
    produtos = Produto.query.all()
    cupons = Cupom.query.all()
    pedidos = Pedido.query.order_by(db.case(
        (Pedido.status == 'Devolução Solicitada', 1),
        (Pedido.status == 'pendente', 2)
    ), Pedido.data_pedido.desc()).all()
    
    return render_template('admin_panel.html', 
                           users=users, 
                           produtos=produtos, 
                           cupons=cupons,
                           pedidos=pedidos)

# --- CRUD de PRODUTOS ---
@app.route('/produto/add', methods=['GET', 'POST'])
@login_required
@seller_required
def add_produto():
    if request.method == 'POST':
        novo_produto = Produto(
            nome=request.form.get('nome'),
            descricao=request.form.get('descricao'),
            preco=request.form.get('preco'),
            estoque=request.form.get('estoque'),
            categoria=request.form.get('categoria'),
            url_imagem=request.form.get('url_imagem'),
            id_vendedor=current_user.id_usuario
        )
        db.session.add(novo_produto)
        db.session.commit()
        flash('Produto adicionado com sucesso!', 'success')
        return redirect(url_for('venda'))
    
    return render_template('add_produto.html')

@app.route('/produto/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@seller_required
def edit_produto(id):
    produto = Produto.query.get_or_404(id)
    
    if produto.id_vendedor != current_user.id_usuario and current_user.tipo_usuario != 'admin':
        flash('Você não tem permissão para editar este produto.', 'danger')
        return redirect(url_for('venda'))
        
    if request.method == 'POST':
        produto.nome = request.form.get('nome')
        produto.descricao = request.form.get('descricao')
        produto.preco = request.form.get('preco')
        produto.estoque = request.form.get('estoque')
        produto.categoria = request.form.get('categoria')
        produto.url_imagem = request.form.get('url_imagem')
        db.session.commit()
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('venda'))
        
    return render_template('edit_produto.html', produto=produto)

@app.route('/produto/delete/<int:id>', methods=['POST'])
@login_required
@seller_required
def delete_produto(id):
    produto = Produto.query.get_or_404(id)
    
    if produto.id_vendedor != current_user.id_usuario and current_user.tipo_usuario != 'admin':
        flash('Você não tem permissão para excluir este produto.', 'danger')
        return redirect(url_for('venda'))

    item_em_pedido = ItensPedido.query.filter_by(id_produto=produto.id_produto).first()
    
    if item_em_pedido:
        flash('Este produto não pode ser excluído pois está associado a pedidos existentes. Considere apenas zerar o estoque.', 'danger')
        return redirect(url_for('venda'))
        
    db.session.delete(produto)
    db.session.commit()
    flash('Produto excluído com sucesso!', 'success')
    return redirect(url_for('venda'))


# --- CRUD de CUPONS ---
@app.route('/admin/cupom/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_cupom():
    if request.method == 'POST':
        novo_cupom = Cupom(
            codigo=request.form.get('codigo'),
            tipo=request.form.get('tipo'),
            valor=request.form.get('valor')
        )
        db.session.add(novo_cupom)
        db.session.commit()
        flash('Cupom adicionado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    
    return render_template('add_cupom.html')

@app.route('/admin/cupom/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_cupom(id):
    cupom = Cupom.query.get_or_404(id)
    if request.method == 'POST':
        cupom.codigo = request.form.get('codigo')
        cupom.tipo = request.form.get('tipo')
        cupom.valor = request.form.get('valor')
        cupom.ativo = request.form.get('ativo') == 'True' 
        
        db.session.commit()
        flash('Cupom atualizado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
        
    return render_template('edit_cupom.html', cupom=cupom)

@app.route('/admin/cupom/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_cupom(id):
    cupom = Cupom.query.get_or_404(id)
    db.session.delete(cupom)
    db.session.commit()
    flash('Cupom excluído com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

# --- CRUD de USUÁRIOS ---
@app.route('/user/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        nome = request.form.get('nome')
        email = request.form.get('email')
        senha = request.form.get('senha')
        tipo_usuario = request.form.get('tipo_usuario')
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Este email já está cadastrado.', 'danger')
            return redirect(url_for('add_user'))
        if not senha:
            flash('O campo senha é obrigatório.', 'danger')
            return redirect(url_for('add_user'))
            
        new_user = User(nome=nome, email=email, senha=senha, tipo_usuario=tipo_usuario)
        db.session.add(new_user)
        db.session.commit()
        new_user.id_usuario = new_user.id
        db.session.commit()
        flash('Usuário criado com sucesso!', 'success')
        return redirect(url_for('admin_panel'))
    return render_template('add_user.html')

@app.route('/user/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    if request.method == 'POST':
        user.nome = request.form.get('nome')
        user.email = request.form.get('email')
        user.tipo_usuario = request.form.get('tipo_usuario')
        nova_senha = request.form.get('senha')
        
        if nova_senha:
            user.set_password(nova_senha)
            flash('Senha do usuário atualizada manualmente.', 'success')
        else:
            flash('Usuário atualizado com sucesso!', 'success')
            
        db.session.commit()
        return redirect(url_for('admin_panel'))
    return render_template('edit_user.html', user=user)

@app.route('/user/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    user_to_delete = User.query.get_or_404(id)
    if user_to_delete.id == current_user.id:
        flash('Você não pode excluir sua própria conta de admin!', 'danger')
        return redirect(url_for('admin_panel'))
    
    # Limpa dependências
    Pedido.query.filter_by(id_usuario=user_to_delete.id_usuario).delete()
    ItemCarrinho.query.filter_by(id_usuario=user_to_delete.id_usuario).delete()
    
    db.session.delete(user_to_delete)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'success')
    return redirect(url_for('admin_panel'))


# --- Ponto de Entrada ---
if __name__ == '__main__':
    app.run(debug=True)