"""Manual add user id fk to emails

Revision ID: 4fe3485197d6
Revises: 
Create Date: 2025-08-26 15:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4fe3485197d6'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### Etape 1: Ajouter la colonne en autorisant les nuls temporairement
    op.add_column('emails', sa.Column('user_id', sa.Integer(), nullable=True))

    # ### Etape 2: Remplir la colonne pour les lignes existantes (on suppose que tout appartient à l'user 1)
    op.execute('UPDATE emails SET user_id = 1')

    # ### Etape 3: Rendre la colonne non-nullable maintenant que tout est rempli
    op.alter_column('emails', 'user_id', nullable=False)

    # ### Etape 4: Créer les index et la clé étrangère
    op.create_index(op.f('ix_emails_user_id'), 'emails', ['user_id'], unique=False)
    op.create_foreign_key('fk_emails_user_id_users', 'emails', 'users', ['user_id'], ['id'])
    
    # Recréation de l'index sur gmail_id pour qu'il ne soit plus unique
    op.drop_index('ix_emails_gmail_id', table_name='emails')
    op.create_index(op.f('ix_emails_gmail_id'), 'emails', ['gmail_id'], unique=False)


def downgrade():
    # On inverse les opérations
    op.drop_index(op.f('ix_emails_gmail_id'), table_name='emails')
    op.create_index('ix_emails_gmail_id', 'emails', ['gmail_id'], unique=True)
    op.drop_constraint('fk_emails_user_id_users', 'emails', type_='foreignkey')
    op.drop_index(op.f('ix_emails_user_id'), table_name='emails')
    op.drop_column('emails', 'user_id')