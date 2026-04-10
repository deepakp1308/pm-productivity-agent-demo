"""Tests for backend.agents.judge — ~5 tests on compute_judge_score()."""

import pytest
from backend.storage.models import JudgeScore
from backend.agents.judge import compute_judge_score


class TestComputeJudgeScore:
    def test_perfect_scores(self):
        """All 3s with no block should yield 5.0."""
        judge = JudgeScore(
            reasoning="Perfect",
            faithfulness=3,
            priority_fit=3,
            specificity=3,
            harm_risk=True,
            privacy_compliance=True,
            block=False,
        )
        assert compute_judge_score(judge) == 5.0

    def test_harm_risk_false_blocks(self):
        """If harm_risk=False the block flag should be True, yielding score 0."""
        judge = JudgeScore(
            reasoning="Harmful",
            faithfulness=3,
            priority_fit=3,
            specificity=3,
            harm_risk=False,
            privacy_compliance=True,
            block=True,
        )
        assert compute_judge_score(judge) == 0.0

    def test_privacy_compliance_false_blocks(self):
        """If privacy_compliance=False the block flag should be True, yielding score 0."""
        judge = JudgeScore(
            reasoning="Privacy issue",
            faithfulness=3,
            priority_fit=3,
            specificity=3,
            harm_risk=True,
            privacy_compliance=False,
            block=True,
        )
        assert compute_judge_score(judge) == 0.0

    def test_any_score_of_one_blocks(self):
        """If any score is 1 the block should be True, yielding 0."""
        judge = JudgeScore(
            reasoning="Low faithfulness",
            faithfulness=1,
            priority_fit=3,
            specificity=3,
            harm_risk=True,
            privacy_compliance=True,
            block=True,
        )
        assert compute_judge_score(judge) == 0.0

    def test_mixed_realistic_scores(self):
        """Mixed scores (2,3,2) unblocked should compute correctly."""
        judge = JudgeScore(
            reasoning="Mixed",
            faithfulness=2,
            priority_fit=3,
            specificity=2,
            harm_risk=True,
            privacy_compliance=True,
            block=False,
        )
        # avg = (2+3+2)/3 = 7/3 ~ 2.333; scaled = 2.333 * 5/3 ~ 3.888 -> rounded to 3.9
        expected = round((2 + 3 + 2) / 3.0 * 5 / 3, 1)
        assert compute_judge_score(judge) == expected
