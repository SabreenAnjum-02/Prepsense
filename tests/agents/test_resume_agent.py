import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agents.resume.agent import ResumeAgent
from agents.shared.types import CandidateProfile

@pytest.fixture
def mock_cleaner():
    cleaner = MagicMock()
    cleaner.clean.return_value = "cleaned text"
    return cleaner

@pytest.fixture
def mock_extractor():
    extractor = MagicMock()
    extractor.extract.return_value = {"name": "John Doe", "skills": ["Python"]}
    return extractor

@pytest.fixture
def mock_parser():
    parser = MagicMock()
    parser.parse.return_value = "raw text"
    return parser

@pytest.fixture
def mock_profiler():
    profiler = MagicMock()
    profiler.build_profile.return_value = CandidateProfile(name="John Doe", skills=["Python"])
    return profiler

@pytest.fixture
def mock_validator():
    validator = MagicMock()
    validator.validate_input.return_value = True
    validator.validate_output.return_value = True
    return validator

@pytest.mark.asyncio
async def test_resume_agent_success(mock_parser, mock_cleaner, mock_extractor, mock_profiler, mock_validator):
    agent = ResumeAgent(
        parser=mock_parser,
        cleaner=mock_cleaner,
        extractor=mock_extractor,
        profiler=mock_profiler
    )
    agent._validator = mock_validator

    input_data = {"file_path": "test.pdf"}
    result = await agent.run(input_data)

    assert result is not None
    assert result.name == "John Doe"
    assert "Python" in result.skills
    mock_parser.parse.assert_called_once_with("test.pdf")
    mock_cleaner.clean.assert_called_once_with("raw text")
    mock_extractor.extract.assert_called_once_with("cleaned text")

@pytest.mark.asyncio
async def test_resume_agent_invalid_input(mock_parser, mock_validator):
    mock_validator.validate_input.return_value = False
    agent = ResumeAgent(parser=mock_parser)
    agent._validator = mock_validator

    with pytest.raises(ValueError, match="Invalid input"):
        await agent.run({"file_path": "invalid.pdf"})

@pytest.mark.asyncio
async def test_resume_agent_invalid_output(mock_parser, mock_cleaner, mock_extractor, mock_profiler, mock_validator):
    mock_validator.validate_output.return_value = False
    agent = ResumeAgent(
        parser=mock_parser,
        cleaner=mock_cleaner,
        extractor=mock_extractor,
        profiler=mock_profiler
    )
    agent._validator = mock_validator

    result = await agent.run({"file_path": "test.pdf"})
    assert result is None
