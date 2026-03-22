"""Initial database schema for Gold Tier Backend

Revision ID: 001_initial
Revises: 
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enums first (with IF NOT EXISTS for safety)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE job_status AS ENUM ('queued', 'processing', 'completed', 'failed', 'pending_approval');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('submitter', 'approver');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pipeline_stage_type AS ENUM (
                'task_analysis', 'plan_creation', 'risk_assessment', 'final_output'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE pipeline_stage_status AS ENUM ('pending', 'running', 'completed', 'failed', 'retrying');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approval_status AS ENUM ('pending', 'approved', 'rejected', 'timeout');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE approval_decision AS ENUM ('approved', 'rejected');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agent_type AS ENUM (
                'task_analyzer', 'planner_agent', 'risk_agent', 'final_output_agent'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE agent_execution_status AS ENUM ('success', 'failure', 'timeout');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('role', sa.Enum('submitter', 'approver', name='user_role'), nullable=False, default='submitter'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_users_email', 'users', ['email'])

    # Jobs table
    op.create_table(
        'jobs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('task_description', sa.Text(), nullable=False),
        sa.Column('status', sa.Enum('queued', 'processing', 'completed', 'failed', 'pending_approval', name='job_status'), nullable=False, default='queued'),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('submitted_by', sa.UUID(), nullable=False),
        sa.Column('submitted_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('parent_job_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_job_id'], ['jobs.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_jobs_status', 'jobs', ['status'])
    op.create_index('ix_jobs_submitted_by', 'jobs', ['submitted_by'])
    op.create_index('ix_jobs_parent_job_id', 'jobs', ['parent_job_id'])
    op.create_index('ix_jobs_submitted_at', 'jobs', ['submitted_at'])

    # Pipeline stages table
    op.create_table(
        'pipeline_stages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('stage_type', sa.Enum('task_analysis', 'plan_creation', 'risk_assessment', 'final_output', name='pipeline_stage_type'), nullable=False),
        sa.Column('status', sa.Enum('pending', 'running', 'completed', 'failed', 'retrying', name='pipeline_stage_status'), nullable=False, default='pending'),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('started_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, default=0),
        sa.Column('timeout_seconds', sa.Integer(), nullable=False, default=30),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pipeline_stages_job_id', 'pipeline_stages', ['job_id'])
    op.create_index('ix_pipeline_stages_stage_type', 'pipeline_stages', ['stage_type'])
    op.create_index('ix_pipeline_stages_status', 'pipeline_stages', ['status'])

    # Plans table
    op.create_table(
        'plans',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False, unique=True),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
        sa.Column('task_analysis', sa.JSON(), nullable=True),
        sa.Column('recommended_actions', sa.JSON(), nullable=True),
        sa.Column('risk_assessment', sa.JSON(), nullable=True),
        sa.Column('approval_status', sa.Enum('pending', 'approved', 'rejected', 'timeout', name='approval_status'), nullable=False, default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_plans_job_id', 'plans', ['job_id'])
    op.create_index('ix_plans_approval_status', 'plans', ['approval_status'])

    # Approval events table
    op.create_table(
        'approval_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('plan_id', sa.UUID(), nullable=False),
        sa.Column('decision', sa.Enum('approved', 'rejected', name='approval_decision'), nullable=False),
        sa.Column('approver_id', sa.UUID(), nullable=False),
        sa.Column('decided_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('comments', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['plans.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['approver_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_approval_events_plan_id', 'approval_events', ['plan_id'])
    op.create_index('ix_approval_events_approver_id', 'approval_events', ['approver_id'])

    # Agent execution logs table
    op.create_table(
        'agent_execution_logs',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('agent_type', sa.Enum('task_analyzer', 'planner_agent', 'risk_agent', 'final_output_agent', name='agent_type'), nullable=False),
        sa.Column('job_id', sa.UUID(), nullable=False),
        sa.Column('stage_id', sa.UUID(), nullable=True),
        sa.Column('input', sa.JSON(), nullable=True),
        sa.Column('output', sa.JSON(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('success', 'failure', 'timeout', name='agent_execution_status'), nullable=False),
        sa.Column('executed_at', sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['stage_id'], ['pipeline_stages.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_agent_execution_logs_job_id', 'agent_execution_logs', ['job_id'])
    op.create_index('ix_agent_execution_logs_stage_id', 'agent_execution_logs', ['stage_id'])
    op.create_index('ix_agent_execution_logs_agent_type', 'agent_execution_logs', ['agent_type'])


def downgrade() -> None:
    # Drop tables in reverse order (foreign key constraints)
    op.drop_table('agent_execution_logs')
    op.drop_table('approval_events')
    op.drop_table('plans')
    op.drop_table('pipeline_stages')
    op.drop_table('jobs')
    op.drop_table('users')
    
    # Drop enums
    op.execute('DROP TYPE agent_execution_status')
    op.execute('DROP TYPE agent_type')
    op.execute('DROP TYPE approval_decision')
    op.execute('DROP TYPE approval_status')
    op.execute('DROP TYPE pipeline_stage_status')
    op.execute('DROP TYPE pipeline_stage_type')
    op.execute('DROP TYPE user_role')
    op.execute('DROP TYPE job_status')
