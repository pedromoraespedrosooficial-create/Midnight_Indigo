from app import app, db
from models import User

# Cria as tabelas
def create_tables():
    print("Conectando ao banco de dados...")
    with app.app_context():
        db.create_all()
    print("Tabelas do Midnight Indigo criadas com sucesso!")

# Cria usuários iniciais
def create_initial_users():
    print("Criando usuário admin...")
    with app.app_context():
        # Verifica se o admin já existe
        admin_user = User.query.filter_by(email='admin@midnight.com').first()
        if not admin_user:
            admin = User(
                nome='Admin', 
                email='admin@midnight.com', 
                senha='admin123', 
                tipo_usuario='admin'
            )
            db.session.add(admin)
            db.session.commit()
            # Precisamos do ID para o id_usuario
            admin.id_usuario = admin.id
            db.session.commit()
            print("Usuário admin (admin@midnight.com / admin123) criado!")
        else:
            print("Usuário admin já existe.")

        print("Criando usuário vendedor de teste...")
        # Verifica se o vendedor já existe
        seller_user = User.query.filter_by(email='vendedor@midnight.com').first()
        if not seller_user:
            seller = User(
                nome='Vendedor Teste', 
                email='vendedor@midnight.com', 
                senha='vendedor123', 
                tipo_usuario='vendedor'
            )
            db.session.add(seller)
            db.session.commit()
            seller.id_usuario = seller.id
            db.session.commit()
            print("Usuário vendedor (vendedor@midnight.com / vendedor123) criado!")
        else:
            print("Usuário vendedor já existe.")

if __name__ == '__main__':
    create_tables()
    create_initial_users()