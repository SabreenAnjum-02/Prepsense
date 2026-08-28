"""001_initial_persistence_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-08-27 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. candidates table
    op.create_table(
        'candidates',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('target_role', sa.String(length=100), nullable=False),
        sa.Column('experience_years', sa.Integer(), nullable=True, default=2),
        sa.Column('skills', sa.JSON(), nullable=True),
        sa.Column('projects', sa.JSON(), nullable=True),
        sa.Column('experience', sa.JSON(), nullable=True),
        sa.Column('target_jd', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidates_email'), 'candidates', ['email'], unique=False)

    # 2. interview_sessions table
    op.create_table(
        'interview_sessions',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('target_role', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, default='CREATED'),
        sa.Column('current_stage', sa.String(length=50), nullable=True, default='INTRODUCTION'),
        sa.Column('current_question_index', sa.Integer(), nullable=True, default=0),
        sa.Column('is_interview_completed', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_practical_completed', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_sessions_candidate_id'), 'interview_sessions', ['candidate_id'], unique=False)

    # 3. interview_turns table
    op.create_table(
        'interview_turns',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('turn_index', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.String(length=100), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('topic', sa.String(length=150), nullable=False),
        sa.Column('difficulty', sa.String(length=50), nullable=True, default='Medium'),
        sa.Column('stage', sa.String(length=50), nullable=True, default='INTRODUCTION'),
        sa.Column('is_followup', sa.Boolean(), nullable=True, default=False),
        sa.Column('candidate_answer', sa.Text(), nullable=True),
        sa.Column('stt_transcript', sa.Text(), nullable=True),
        sa.Column('time_taken_seconds', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_interview_turns_session_id'), 'interview_turns', ['session_id'], unique=False)
    op.create_index('ix_turn_session_turn_index', 'interview_turns', ['session_id', 'turn_index'], unique=False)

    # 4. evaluations table
    op.create_table(
        'evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('turn_id', sa.String(length=36), nullable=True),
        sa.Column('question_id', sa.String(length=100), nullable=False),
        sa.Column('technical_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('practical_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('problem_solving_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('communication_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('behavioral_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('role_fit_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('overall_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('confidence_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('weaknesses', sa.JSON(), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('criterion_evaluations', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['turn_id'], ['interview_turns.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evaluations_session_id'), 'evaluations', ['session_id'], unique=False)
    op.create_index(op.f('ix_evaluations_turn_id'), 'evaluations', ['turn_id'], unique=False)

    # 5. practical_evaluations table
    op.create_table(
        'practical_evaluations',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('task_id', sa.String(length=100), nullable=False),
        sa.Column('task_title', sa.String(length=255), nullable=False),
        sa.Column('role_archetype', sa.String(length=100), nullable=False),
        sa.Column('language', sa.String(length=50), nullable=True, default='python'),
        sa.Column('tests_passed', sa.Integer(), nullable=True, default=0),
        sa.Column('total_tests', sa.Integer(), nullable=True, default=0),
        sa.Column('hidden_tests_passed', sa.Integer(), nullable=True, default=0),
        sa.Column('total_hidden_tests', sa.Integer(), nullable=True, default=0),
        sa.Column('correctness_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('edge_case_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('complexity_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('code_quality_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('overall_practical_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('time_complexity', sa.String(length=50), nullable=True, default='N/A'),
        sa.Column('space_complexity', sa.String(length=50), nullable=True, default='N/A'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('execution_results', sa.JSON(), nullable=True),
        sa.Column('submission_code', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_practical_evaluations_session_id'), 'practical_evaluations', ['session_id'], unique=True)

    # 6. final_reports table
    op.create_table(
        'final_reports',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('session_id', sa.String(length=36), nullable=False),
        sa.Column('candidate_id', sa.String(length=36), nullable=False),
        sa.Column('overall_summary', sa.Text(), nullable=False),
        sa.Column('technical_assessment', sa.Text(), nullable=False),
        sa.Column('communication_assessment', sa.Text(), nullable=False),
        sa.Column('hiring_recommendation', sa.String(length=50), nullable=False),
        sa.Column('confidence_level', sa.String(length=50), nullable=False),
        sa.Column('final_score', sa.Float(), nullable=True, default=0.0),
        sa.Column('dimension_scores', sa.JSON(), nullable=True),
        sa.Column('strengths', sa.JSON(), nullable=True),
        sa.Column('weaknesses', sa.JSON(), nullable=True),
        sa.Column('improvement_plan', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'], ['interview_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_final_reports_candidate_id'), 'final_reports', ['candidate_id'], unique=False)
    op.create_index(op.f('ix_final_reports_session_id'), 'final_reports', ['session_id'], unique=True)


def downgrade() -> None:
    op.drop_table('final_reports')
    op.drop_table('practical_evaluations')
    op.drop_table('evaluations')
    op.drop_table('interview_turns')
    op.drop_table('interview_sessions')
    op.drop_table('candidates')
