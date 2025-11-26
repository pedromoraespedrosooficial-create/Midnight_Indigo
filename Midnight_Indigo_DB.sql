CREATE DATABASE Midnight_Indigo_DB;
USE Midnight_Indigo_DB;
/* 1. Apaga o banco de dados antigo (e todos os seus dados) */
DROP DATABASE Midnight_Indigo_DB;


/* 1. MUITO IMPORTANTE: Mude para o banco 'master' */
USE master;
GO

/* 2. Força o banco a entrar em modo "usuário único" e derruba todas as outras conexões IMEDIATAMENTE */
ALTER DATABASE Midnight_Indigo_DB
SET SINGLE_USER
WITH ROLLBACK IMMEDIATE;
GO

/* 3. Agora você pode deletar */
DROP DATABASE Midnight_Indigo_DB;
GO

/* 4. Crie o banco novamente */
CREATE DATABASE Midnight_Indigo_DB;
GO