
from database import (
    get_stats,
    active_visits,
    visit_history
)


class CustomerAgent:

    def answer_question(self, question):

        question = question.lower().strip()

        stats = get_stats()

        # 1. Tổng số khách hàng
        if "tổng khách hàng" in question:
            return (
                f"Hệ thống hiện có "
                f"{stats['total_customers']} khách hàng."
            )

        # 2. Khách đang trong phòng
        if "đang trong phòng" in question:

            visitors = active_visits()

            if not visitors:
                return "Hiện không có khách trong phòng."

            names = [
                item["full_name"]
                for item in visitors
            ]

            return (
                f"Hiện có {len(names)} khách trong phòng: "
                + ", ".join(names)
            )

        # 3. Lượt vào hôm nay
        if "hôm nay" in question:

            return (
                f"Hôm nay có "
                f"{stats['today_visits']} lượt khách vào."
            )

        # 4. Lịch sử
        if "lịch sử" in question:

            history = visit_history(10)

            if not history:
                return "Chưa có lịch sử ra vào."

            result = []

            for item in history:
                result.append(
                    f"{item['full_name']}: "
                    f"Vào {item['check_in']}, "
                    f"Ra {item['check_out'] or 'Chưa ghi nhận'}"
                )

            return "\n".join(result)

        return (
            "Tôi chưa hiểu câu hỏi. "
            "Bạn có thể hỏi về tổng khách hàng, "
            "khách đang trong phòng, lượt vào hôm nay "
            "hoặc lịch sử ra vào."
        )
