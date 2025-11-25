# from complex_functions import analyze_text_sentiment
import pytest

from data.raw.simple.simple2 import analyze_text_sentiment


class TestAnalyzeTextSentiment:
    """测试文本情感分析函数"""

    def test_positive_sentiment_with_high_confidence(self):
        """测试积极情感文本，高置信度"""
        text = "This is a good and excellent product. I love it!"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "positive"
        assert result["confidence"] > 0.5
        assert isinstance(result["sentiment"], str)
        assert isinstance(result["confidence"], float)

    def test_negative_sentiment_with_high_confidence(self):
        """测试消极情感文本，高置信度"""
        text = "This is a bad and terrible product. I hate it!"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "negative"
        assert result["confidence"] > 0.5
        assert isinstance(result["sentiment"], str)
        assert isinstance(result["confidence"], float)

    def test_neutral_sentiment_no_keywords(self):
        """测试中性情感文本，无关键词"""
        text = "The weather is nice today."
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 1.0

    def test_neutral_sentiment_equal_counts(self):
        """测试中性情感文本，积极和消极关键词数量相等"""
        text = "I love the design but hate the price. Good quality but bad service."
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"
        assert 0 < result["confidence"] < 1.0

    def test_case_insensitivity(self):
        """测试大小写不敏感性"""
        text = "GOOD BAD Excellent Terrible"
        result = analyze_text_sentiment(text)

        # 应该检测到所有关键词，但由于数量相等，应为中性
        assert result["sentiment"] == "neutral"

    def test_empty_string(self):
        """测试空字符串"""
        text = ""
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 1.0

    def test_only_punctuation(self):
        """测试只有标点符号的文本"""
        text = "!!! ??? ... ,,,"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 1.0

    def test_mixed_case_keywords(self):
        """测试混合大小写关键词"""
        text = "GoOd BaD ExCeLlEnT TeRrIbLe"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"

    def test_single_positive_word(self):
        """测试单个积极词汇"""
        text = "good"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "positive"
        assert result["confidence"] == 1.0

    def test_single_negative_word(self):
        """测试单个消极词汇"""
        text = "bad"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "negative"
        assert result["confidence"] == 1.0

    def test_multiple_occurrences_same_word(self):
        """测试同一词汇多次出现"""
        text = "good good good good bad"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "positive"
        assert result["confidence"] == 0.6  # (4-1)/5 = 0.6

    def test_words_within_words(self):
        """测试词汇作为其他词汇的一部分"""
        text = "goodness badminton excellent terriblely"
        result = analyze_text_sentiment(text)

        # 由于使用了单词边界匹配，这些不应该被识别为关键词
        assert result["sentiment"] == "neutral"
        assert result["confidence"] == 1.0

    def test_special_characters_with_words(self):
        """测试包含特殊字符的文本"""
        text = "This is good! But also bad... Excellent? Terrible!"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"

    def test_numeric_text(self):
        """测试包含数字的文本"""
        text = "123 good 456 bad 789"
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "neutral"

    def test_very_long_text(self):
        """测试非常长的文本"""
        text = "good " * 100 + "bad " * 50
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "positive"
        assert result["confidence"] == pytest.approx(
            0.333, abs=0.001
        )  # (100-50)/150 ≈ 0.333

    def test_confidence_calculation_accuracy(self):
        """测试置信度计算的准确性"""
        text = "good good bad"  # 2 positive, 1 negative
        result = analyze_text_sentiment(text)

        expected_confidence = (2 - 1) / 3  # 0.333...
        assert result["confidence"] == pytest.approx(expected_confidence, abs=0.001)
        assert result["sentiment"] == "positive"

    def test_all_positive_words(self):
        """测试所有预定义的积极词汇"""
        positive_words = [
            "good",
            "great",
            "excellent",
            "happy",
            "positive",
            "best",
            "love",
            "like",
        ]
        text = " ".join(positive_words)
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "positive"
        assert result["confidence"] == 1.0

    def test_all_negative_words(self):
        """测试所有预定义的消极词汇"""
        negative_words = [
            "bad",
            "terrible",
            "awful",
            "sad",
            "negative",
            "worst",
            "hate",
            "dislike",
        ]
        text = " ".join(negative_words)
        result = analyze_text_sentiment(text)

        assert result["sentiment"] == "negative"
        assert result["confidence"] == 1.0

    def test_return_type_structure(self):
        """测试返回值的类型和结构"""
        text = "test text"
        result = analyze_text_sentiment(text)

        assert isinstance(result, dict)
        assert set(result.keys()) == {"sentiment", "confidence"}
        assert result["sentiment"] in {"positive", "negative", "neutral"}
        assert 0 <= result["confidence"] <= 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
