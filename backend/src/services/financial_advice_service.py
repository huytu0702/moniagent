"""
Financial Advice Service for generating AI-driven financial advice
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from src.models.expense import Expense
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage


logger = logging.getLogger(__name__)


class FinancialAdviceServiceError(Exception):
    """Custom exception for financial advice service errors"""

    pass


class FinancialAdviceService:
    """
    Service for generating AI-driven financial advice based on spending patterns
    """

    def __init__(self):
        try:
            # Use ChatGoogleGenerativeAI following existing codebase pattern
            self.ai_client = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash", temperature=0.3
            )
            # Use lite model for simple analysis
            self.lite_client = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash-lite", temperature=0.1
            )
            logger.info("FinancialAdviceService initialized with Gemini AI clients")
        except Exception as e:
            logger.warning(f"Failed to initialize AI client: {str(e)}")
            self.ai_client = None
            self.lite_client = None

    def get_financial_advice(
        self,
        user_id: str,
        period: str = "monthly",
        db_session: Session = None,
    ) -> Dict[str, Any]:
        """
        Generate financial advice for a user based on their spending patterns

        Args:
            user_id: ID of the user
            period: Time period to analyze (daily, weekly, monthly)
            db_session: Database session

        Returns:
            Dictionary with advice, recommendations, and spending pattern analysis
        """
        try:
            logger.info(
                f"Generating financial advice for user {user_id}, period {period}"
            )

            # Get spending analysis
            spending_analysis = self._analyze_spending(user_id, period, db_session)

            # Generate advice using AI
            advice_result = self._generate_ai_advice(user_id, spending_analysis)
            
            # Include spending analysis in the result
            advice_result["spending_analysis"] = spending_analysis

            return advice_result

        except Exception as e:
            logger.error(f"Error generating financial advice: {str(e)}")
            raise FinancialAdviceServiceError(
                f"Failed to generate financial advice: {str(e)}"
            )

    def _analyze_spending(
        self,
        user_id: str,
        period: str,
        db_session: Session,
    ) -> Dict[str, Any]:
        """
        Analyze user spending patterns

        Args:
            user_id: ID of the user
            period: Time period to analyze
            db_session: Database session

        Returns:
            Dictionary with spending analysis data
        """
        try:
            today = datetime.utcnow().date()

            if period == "daily":
                start_date = today
                end_date = today
            elif period == "weekly":
                start_date = today - timedelta(days=today.weekday())
                end_date = start_date + timedelta(days=6)
            else:  # monthly
                start_date = today.replace(day=1)
                if today.month == 12:
                    end_date = today.replace(
                        year=today.year + 1, month=1, day=1
                    ) - timedelta(days=1)
                else:
                    end_date = today.replace(month=today.month + 1, day=1) - timedelta(
                        days=1
                    )

            analysis = {
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "total_spending": 0.0,
                "by_category": {},
                "average_daily": 0.0,
                "top_category": None,
                "top_amount": 0.0,
            }

            if db_session:
                expenses = (
                    db_session.query(Expense)
                    .filter(
                        Expense.user_id == user_id,
                        Expense.date >= start_date,
                        Expense.date <= end_date,
                    )
                    .all()
                )

                for expense in expenses:
                    analysis["total_spending"] += expense.amount
                    # Use category name (string), not Category object
                    category_name = (
                        expense.category.name if expense.category else "Uncategorized"
                    )
                    if category_name not in analysis["by_category"]:
                        analysis["by_category"][category_name] = 0.0
                    analysis["by_category"][category_name] += expense.amount

                # Find top spending category
                if analysis["by_category"]:
                    analysis["top_category"] = max(
                        analysis["by_category"], key=analysis["by_category"].get
                    )
                    analysis["top_amount"] = analysis["by_category"][
                        analysis["top_category"]
                    ]

                # Calculate average daily spending
                num_days = (end_date - start_date).days + 1
                analysis["average_daily"] = (
                    analysis["total_spending"] / num_days if num_days > 0 else 0.0
                )
            else:
                # Default mock analysis
                analysis["total_spending"] = 1500.0
                analysis["by_category"] = {
                    "Eating Out": 500.0,
                    "Transportation": 600.0,
                    "Entertainment": 400.0,
                }
                analysis["average_daily"] = 50.0
                analysis["top_category"] = "Transportation"
                analysis["top_amount"] = 600.0

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing spending: {str(e)}")
            return {
                "period": period,
                "total_spending": 0.0,
                "by_category": {},
                "average_daily": 0.0,
                "top_category": None,
            }

    def _generate_ai_advice(
        self,
        user_id: str,
        spending_analysis: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate AI-driven advice based on spending analysis

        Args:
            user_id: ID of the user
            spending_analysis: Dictionary with spending data

        Returns:
            Dictionary with advice and recommendations
        """
        try:
            # Determine spending pattern
            spending_pattern = self._determine_spending_pattern(spending_analysis)

            # Create AI prompt
            prompt = self._create_advice_prompt(spending_analysis, spending_pattern)

            # Generate advice using AI (if available)
            if self.ai_client:
                try:
                    advice_text = self._call_ai_api(prompt)
                except Exception as ai_error:
                    logger.warning(
                        f"AI API call failed: {str(ai_error)}, using default advice"
                    )
                    advice_text = self._get_default_advice(
                        spending_analysis, spending_pattern
                    )
            else:
                advice_text = self._get_default_advice(
                    spending_analysis, spending_pattern
                )

            # Parse recommendations from advice
            recommendations = self._extract_recommendations(advice_text)

            return {
                "advice": advice_text,
                "recommendations": recommendations,
                "spending_pattern": spending_pattern,
                "period": spending_analysis.get("period", "monthly"),
                "top_spending_category": spending_analysis.get("top_category"),
                "top_spending_amount": spending_analysis.get("top_amount"),
            }

        except Exception as e:
            logger.error(f"Error generating AI advice: {str(e)}")
            # Return default advice
            return {
                "advice": "Track your spending regularly and set budget limits for each category.",
                "recommendations": [
                    "Monitor your expenses weekly",
                    "Set realistic budget goals",
                    "Review and adjust spending habits monthly",
                ],
                "spending_pattern": "normal",
                "period": spending_analysis.get("period", "monthly"),
                "top_spending_category": spending_analysis.get("top_category"),
                "top_spending_amount": spending_analysis.get("top_amount"),
            }

    def _determine_spending_pattern(self, analysis: Dict[str, Any]) -> str:
        """
        Determine spending pattern based on analysis (Vietnam context)

        Args:
            analysis: Spending analysis dictionary

        Returns:
            Spending pattern string: 'low', 'normal', 'high', 'above_average'
        """
        try:
            total = analysis.get("total_spending", 0)
            average_daily = analysis.get("average_daily", 0)

            # Vietnam context: Adjusted thresholds based on local economy
            # Assuming amounts are in VND
            if total == 0:
                return "low"
            elif average_daily < 200000:  # < 200k VND/day (~$8)
                return "low"
            elif average_daily < 400000:  # < 400k VND/day (~$16)
                return "normal"
            elif average_daily < 700000:  # < 700k VND/day (~$28)
                return "above_average"
            else:
                return "high"

        except Exception as e:
            logger.error(f"Error determining spending pattern: {str(e)}")
            return "normal"

    def _create_advice_prompt(
        self,
        analysis: Dict[str, Any],
        pattern: str,
    ) -> str:
        """
        Create AI prompt for generating advice

        Args:
            analysis: Spending analysis data
            pattern: Spending pattern

        Returns:
            Prompt string for AI
        """
        categories_str = ", ".join(
            [
                f"{cat}: {amount:,.0f}đ"
                for cat, amount in analysis.get("by_category", {}).items()
            ]
        )
        
        period_label = {
            "daily": "ngày",
            "weekly": "tuần này",
            "monthly": "tháng này"
        }.get(analysis.get("period", "monthly"), "tháng này")

        prompt = f"""Bạn là chuyên gia tư vấn tài chính cá nhân tại Việt Nam. Người dùng đã yêu cầu lời khuyên về chi tiêu của họ.

**Phân tích chi tiêu {period_label}:**
- Tổng chi tiêu: {analysis.get('total_spending', 0):,.0f}đ
- Chi tiêu trung bình/ngày: {analysis.get('average_daily', 0):,.0f}đ  
- Chi tiêu theo danh mục: {categories_str if categories_str else "Chưa có dữ liệu"}
- Mức độ chi tiêu: {pattern}

**Yêu cầu lời khuyên toàn diện:**
1. Đánh giá tổng quan về thói quen chi tiêu
2. Phân tích chi tiêu theo từng danh mục chính
3. Những điểm tốt và cần cải thiện
4. Khuyến nghị cụ thể và thực tế để quản lý chi tiêu tốt hơn  
5. Mục tiêu ngắn hạn nếu phù hợp

**Hướng dẫn chi tiết:**
- Nếu chi tiêu ăn uống cao: gợi ý tự nấu ăn, meal prep, giảm ăn ngoài
- Nếu chi tiêu đi lại cao: gợi ý sử dụng xe buýt, xe đạp, carpooling
- Nếu chi tiêu mua sắm cao: gợi ý lập danh sách, so sánh giá, chờ đợt sale
- Nếu chi tiêu giải trí cao: gợi ý các hoạt động miễn phí, giảm tần suất

Lời khuyên cần:
- Thân thiện, dễ hiểu, bằng tiếng Việt
- Cụ thể và có thể thực hiện được
- Phù hợp với bối cảnh Việt Nam
- Tích cực và khích lệ người dùng

Trả lời bằng văn xuôi tự nhiên, KHÔNG dùng format markdown hoặc bullet points trong phần lời khuyên chính."""
        return prompt

    def _call_ai_api(self, prompt: str) -> str:
        """
        Call AI API to generate advice

        Args:
            prompt: Prompt for AI

        Returns:
            AI-generated advice text
        """
        try:
            if not self.ai_client:
                raise FinancialAdviceServiceError("AI client not available")

            # Call AI API using LangChain pattern with max_tokens for comprehensive advice
            response = self.ai_client.invoke(
                [HumanMessage(content=prompt)],
                max_tokens=2000  # Allow longer, more detailed advice
            )
            advice_text = response.content.strip()

            logger.info(f"Generated AI advice: {advice_text[:100]}...")
            return advice_text

        except Exception as e:
            logger.error(f"Error calling AI API: {str(e)}")
            raise

    def _get_default_advice(
        self,
        analysis: Dict[str, Any],
        pattern: str,
    ) -> str:
        """
        Get default advice if AI is not available

        Args:
            analysis: Spending analysis data
            pattern: Spending pattern

        Returns:
            Default advice string
        """
        top_category = analysis.get("top_category", "chi tiêu của bạn")

        if pattern == "high":
            return f"Chi tiêu của bạn ở danh mục {top_category} đang khá cao. Bạn nên đặt giới hạn ngân sách nghiêm ngặt hơn và tìm kiếm các phương án thay thế để giảm chi tiêu trong danh mục này."
        elif pattern == "above_average":
            return f"Chi tiêu của bạn ở danh mục {top_category} cao hơn trung bình. Hãy tìm cơ hội để tối ưu hóa danh mục này nhằm cải thiện sức khỏe tài chính."
        elif pattern == "normal":
            return f"Mức chi tiêu của bạn khá lành mạnh. Tiếp tục theo dõi {top_category} và duy trì kỷ luật tài chính hiện tại."
        else:
            return "Duy trì thói quen chi tiêu hiện tại và tiếp tục theo dõi chi tiêu thường xuyên để nâng cao nhận thức tài chính."

    def _extract_recommendations(self, advice_text: str) -> List[str]:
        """
        Extract specific recommendations from advice text

        Args:
            advice_text: Generated advice text

        Returns:
            List of recommendation strings
        """
        try:
            # Simple extraction of bullet points or sentences
            recommendations = []

            # Look for numbered items or bullet points
            lines = advice_text.split("\n")
            for line in lines:
                line = line.strip()
                if line and (
                    line[0].isdigit()
                    or line.startswith("-")
                    or line.startswith("•")
                    or line.startswith("*")
                ):
                    # Remove numbering or bullets
                    recommendation = line.lstrip("0123456789.-•*").strip()
                    if (
                        recommendation and len(recommendation) > 5
                    ):  # Filter out very short lines
                        recommendations.append(recommendation)

            # If no bullet points found, try to extract using AI for better parsing
            if not recommendations and self.lite_client:
                try:
                    extract_prompt = f"""Từ đoạn lời khuyên tài chính sau, hãy trích xuất 3 gợi ý cụ thể nhất:

"{advice_text}"

Trả về JSON format (không markdown):
{{
  "recommendations": [
    "Gợi ý 1",
    "Gợi ý 2", 
    "Gợi ý 3"
  ]
}}"""

                    response = self.lite_client.invoke(
                        [HumanMessage(content=extract_prompt)]
                    )
                    import json

                    result = json.loads(response.content.strip())
                    recommendations = result.get("recommendations", [])
                except Exception as extract_error:
                    logger.warning(f"AI extraction failed: {str(extract_error)}")

            # If still no recommendations, split into sentences and take first 3
            if not recommendations:
                sentences = [
                    s.strip() + "."
                    for s in advice_text.split(".")
                    if s.strip() and len(s.strip()) > 10
                ]
                recommendations = sentences[:3]

            return recommendations[:3]  # Return top 3 recommendations

        except Exception as e:
            logger.error(f"Error extracting recommendations: {str(e)}")
            return [
                "Theo dõi chi tiêu thường xuyên",
                "Đặt giới hạn ngân sách cho từng danh mục",
                "Xem xét và điều chỉnh hàng tháng",
            ]
