import os
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.sql import func
from sqlalchemy.orm import foreign

db = SQLAlchemy()

# --- TABELA DE USUÁRIOS (Adaptada) ---
class User(db.Model, UserMixin):
    __tablename__ = 'Usuarios'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, unique=True)
    nome = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha_hash = db.Column(db.String(200), nullable=False)
    
    # 'cliente', 'vendedor', 'admin'
    tipo_usuario = db.Column(db.String(10), nullable=False, default='cliente')
    
    # Relações de E-commerce
    pedidos = db.relationship('Pedido', backref='comprador', lazy=True, cascade="all, delete-orphan")
    carrinho = db.relationship('ItemCarrinho', backref='usuario', lazy=True, cascade="all, delete-orphan")
    produtos_venda = db.relationship('Produto', backref='vendedor', lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        return str(self.id_usuario)

    def __init__(self, **kwargs):
        senha = kwargs.pop('senha', None)
        super(User, self).__init__(**kwargs)
        if self.id:
            self.id_usuario = self.id
        if senha:
            self.set_password(senha)

    def set_password(self, senha):
        self.senha_hash = generate_password_hash(senha)

    def check_password(self, senha):
        return check_password_hash(self.senha_hash, senha)

# --- TABELA DE PRODUTOS (Nova - Substitui Filme/Serie) ---
class Produto(db.Model):
    __tablename__ = 'Produtos'
    id_produto = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    id_vendedor = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    
    nome = db.Column(db.String(200), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    preco = db.Column(db.Numeric(10, 2), nullable=False)
    estoque = db.Column(db.Integer, nullable=False, default=1)
    
    # ========================================
    #               (CORRIGIDO)
    # Aumentado de 100 para 300 caracteres
    # ========================================
    categoria = db.Column(db.String(300), nullable=False) 
    
    url_imagem = db.Column(db.String(400), nullable=True)
    data_cadastro = db.Column(db.DateTime(timezone=True), server_default=func.now())
    
    # Relações
    itens_pedido = db.relationship('ItensPedido', backref='produto', lazy=True) 
    itens_carrinho = db.relationship('ItemCarrinho', backref='produto', lazy=True, cascade="all, delete-orphan")

# --- TABELA DE CUPONS (Nova - Requisito) ---
class Cupom(db.Model):
    __tablename__ = 'Cupons'
    id_cupom = db.Column(db.Integer, primary_key=True, autoincrement=True)
    codigo = db.Column(db.String(50), unique=True, nullable=False)
    # 'porcentagem' (ex: 10 para 10%) ou 'fixo' (ex: 50 para R$ 50,00)
    tipo = db.Column(db.String(20), nullable=False, default='porcentagem')
    valor = db.Column(db.Numeric(10, 2), nullable=False)
    ativo = db.Column(db.Boolean, default=True)

# --- TABELAS DE PEDIDOS (Novas - Requisito) ---
class Pedido(db.Model):
    __tablename__ = 'Pedidos'
    id_pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    data_pedido = db.Column(db.DateTime(timezone=True), server_default=func.now())
    # 'pendente', 'pago', 'enviado', 'concluido', 'cancelado', 'Devolução Solicitada'
    status = db.Column(db.String(20), nullable=False, default='pendente')
    valor_total = db.Column(db.Numeric(10, 2), nullable=False)
    
    itens = db.relationship('ItensPedido', backref='pedido', lazy=True, cascade="all, delete-orphan")

class ItensPedido(db.Model):
    __tablename__ = 'ItensPedido'
    id_item_pedido = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_pedido = db.Column(db.Integer, db.ForeignKey('Pedidos.id_pedido'), nullable=False)
    id_produto = db.Column(db.Integer, db.ForeignKey('Produtos.id_produto'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False)
    preco_unitario = db.Column(db.Numeric(10, 2), nullable=False) 

# --- TABELA DE CARRINHO (Nova - Substitui Favoritos) ---
class ItemCarrinho(db.Model):
    __tablename__ = 'ItensCarrinho'
    id_item_carrinho = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_usuario = db.Column(db.Integer, db.ForeignKey('Usuarios.id_usuario'), nullable=False)
    id_produto = db.Column(db.Integer, db.ForeignKey('Produtos.id_produto'), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=1)
    data_adicionado = db.Column(db.DateTime(timezone=True), server_default=func.now())